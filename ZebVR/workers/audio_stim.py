from dagline import WorkerNode
import matplotlib.pyplot as plt
from scipy.signal import spectrogram, welch
from multiprocessing import RawValue, Process, Queue, Event
from multiprocessing.synchronize  import Event as EventType
import queue
from ZebVR.protocol import DEFAULT, Stim, ClickPolarity, SweepType
from typing import Dict, Any
import time
import os
import sounddevice as sd
import numpy as np
from numpy.typing import NDArray

def plot_waveform_spectrogram_and_psd(
        signal: np.ndarray,
        samplerate: int = 44100,
        max_freq: float = 8000,
        title_prefix: str = "Audio Signal",
        cmap: str = "magma"
    ) -> None:
    """
    Plot waveform, spectrogram, and power spectrum of an audio signal.

    Parameters:
        signal (np.ndarray): 1D audio signal.
        samplerate (int): Sampling rate in Hz.
        max_freq (float): Max frequency for y-axis in Hz (for plots).
        title_prefix (str): Title prefix for each plot.
        cmap (str): Colormap for spectrogram.
    """
    # Time axis
    duration = len(signal) / samplerate
    time = np.linspace(0, duration, len(signal), endpoint=False)

    # Spectrogram
    f, t, Sxx = spectrogram(signal, fs=samplerate, nperseg=1024, noverlap=512)
    Sxx_dB = 10 * np.log10(Sxx + 1e-12)

    # Power Spectral Density
    freqs, psd = welch(signal, fs=samplerate, nperseg=4096)
    psd_dB = 10 * np.log10(psd + 1e-12)

    # Plot
    fig, axs = plt.subplots(3, 1, figsize=(12, 10), constrained_layout=True)

    # Waveform
    axs[0].plot(time, signal, color='black', linewidth=0.7)
    axs[0].set_title(f"{title_prefix} – Waveform")
    axs[0].set_ylabel("Amplitude")
    axs[0].set_xlim([0, duration])

    # Spectrogram
    pcm = axs[1].pcolormesh(t, f, Sxx_dB, shading='gouraud', cmap=cmap)
    axs[1].set_title(f"{title_prefix} – Spectrogram")
    axs[1].set_ylabel("Frequency [Hz]")
    axs[1].set_ylim([0, max_freq])
    fig.colorbar(pcm, ax=axs[1], label="Power [dB/Hz]")

    # Power Spectrum
    axs[2].semilogx(freqs, psd_dB, color='navy')
    axs[2].set_title(f"{title_prefix} – Power Spectrum")
    axs[2].set_xlabel("Frequency [Hz]")
    axs[2].set_ylabel("PSD [dB/Hz]")
    axs[2].grid(True, which='both', ls='--', lw=0.5)
    axs[2].set_xlim(10, samplerate / 2)
    axs[2].set_ylim(np.max(psd_dB) - 60, np.max(psd_dB) + 3)

    plt.show()

class SharedAudioParameters:

    def __init__(self):
        
        self.stim_select = RawValue('d', Stim.SILENCE) 
        self.phototaxis_polarity = RawValue('d', DEFAULT['phototaxis_polarity'])
        self.frequency_Hz = RawValue('d', DEFAULT['frequency_Hz'])
        self.amplitude_dB_SPL = RawValue('d', DEFAULT['amplitude_dB_SPL'])
        self.f_start = RawValue('d', DEFAULT['f_start'])
        self.f_stop = RawValue('d', DEFAULT['f_stop'])
        self.method = RawValue('d', DEFAULT['method'])
        self.click_rate = RawValue('d', DEFAULT['click_rate'])
        self.click_amplitude = RawValue('d', DEFAULT['click_amplitude'])
        self.click_duration = RawValue('d', DEFAULT['click_duration'])
        self.polarity = RawValue('d', DEFAULT['polarity'])

    def from_dict(self, d: Dict) -> None:

        self.stim_select.value = d.get('stim_select', Stim.SILENCE)
        self.phototaxis_polarity.value = d.get('phototaxis_polarity', DEFAULT['phototaxis_polarity'])
        self.frequency_Hz.value = d.get('frequency_Hz', DEFAULT['frequency_Hz'])
        self.amplitude_dB_SPL.value = d.get('amplitude_dB_SPL', DEFAULT['amplitude_dB_SPL'])
        self.f_start.value = d.get('f_start', DEFAULT['f_start'])
        self.f_stop.value = d.get('f_stop', DEFAULT['f_stop'])
        self.method.value = d.get('method', DEFAULT['method'])
        self.click_rate.value = d.get('click_rate', DEFAULT['click_rate'])
        self.click_amplitude.value = d.get('click_amplitude', DEFAULT['click_amplitude'])
        self.click_duration.value = d.get('click_duration', DEFAULT['click_duration'])
        self.polarity.value = d.get('polarity', DEFAULT['polarity'])

class AudioProducer(Process):
    
    def __init__(
            self, 
            audio_queue: Queue, 
            stop_event: EventType,
            shared_audio_parameters: SharedAudioParameters,
            samplerate: int = 44100,
            blocksize: int = 1024,
            channels: int = 1
        ):

        super().__init__()

        self.stop_event = stop_event
        self.audio_queue = audio_queue
        self.samplerate = samplerate
        self.blocksize = blocksize 
        self.channels = channels
        self.shared_audio_parameters = shared_audio_parameters 

        self.phase: int = 0
        self.chunk_function = self._silence

    def _silence(self) -> NDArray:
        return np.zeros((self.blocksize, self.channels), dtype=np.float32)
    
    def _pure_tone(self) -> NDArray:
        frequency = self.shared_audio_parameters.frequency_Hz.value
        amplitude = self.shared_audio_parameters.amplitude_dB_SPL.value

        t = (np.arange(self.blocksize) + self.phase) / self.samplerate
        chunk = amplitude * np.sin(2 * np.pi * frequency * t)
        if self.channels > 1:
            chunk = np.tile(chunk[:, None], (1, self.channels))
        self.phase = (self.phase + self.blocksize) % self.samplerate
        return chunk

    def _frequency_sweep(self) -> NDArray:
        f_start = self.shared_audio_parameters.f_start.value
        f_stop = self.shared_audio_parameters.f_stop.value
        amplitude = self.shared_audio_parameters.amplitude_dB_SPL.value
        method = SweepType(self.shared_audio_parameters.method.value) 

        t = np.arange(self.blocksize + self.phase) / self.samplerate

        if method == SweepType.LINEAR:
            phase_array = 2 * np.pi * (f_start * t + (f_stop - f_start) / 2 * t**2)
        elif method == SweepType.LOG:
            if f_start <= 0 or f_stop <= 0:
                raise ValueError("Log sweep requires positive frequencies")
            k = np.log(f_stop / f_start)
            phase_array = 2 * np.pi * f_start * (np.exp(k * t) - 1) / k
        else:
            raise ValueError("Unsupported method. Choose 'linear' or 'log'.")

        chunk = amplitude * np.sin(phase_array)
        if self.channels > 1:
            chunk = np.tile(chunk[:, None], (1, self.channels))
        
        self.phase = (self.phase + self.blocksize) % self.samplerate
        return chunk

    def _white_noise(self) -> NDArray:
        amplitude = self.shared_audio_parameters.amplitude_dB_SPL.value

        chunk = amplitude * np.random.randn(self.blocksize).astype(np.float32)
        if self.channels > 1:
            chunk = np.tile(chunk[:, None], (1, self.channels))
        return chunk
    
    def _pink_noise(self) -> NDArray:
        # pink noise approximation using Paul Kellet's economy filter
        # https://www.firstpr.com.au/dsp/pink-noise/#Filtering
        # Optimized for a 44100Hz samplerate

        amplitude = self.shared_audio_parameters.amplitude_dB_SPL.value

        white = np.random.randn(self.blocksize).astype(np.float32)
        pink = np.zeros_like(white)
        x0, x1, x2 = 0.0, 0.0, 0.0
        for i in range(self.blocksize):
            x0 = 0.99765 * x0 + white[i] * 0.0990460
            x1 = 0.96300 * x1 + white[i] * 0.2965164
            x2 = 0.57000 * x2 + white[i] * 1.0526913
            pink[i] = x0 + x1 + x2 + white[i] * 0.1848

        chunk = amplitude * pink
        if self.channels > 1:
            chunk = np.tile(chunk[:, None], (1, self.channels))
        return chunk
    
    def _click_train(self) -> NDArray:
        click_rate = self.shared_audio_parameters.click_rate.value
        click_amplitude = self.shared_audio_parameters.click_amplitude.value
        click_duration = self.shared_audio_parameters.click_duration.value
        polarity = ClickPolarity(self.shared_audio_parameters.polarity.value)

        interval_samples = int(self.samplerate / click_rate)
        click_samples = int(self.samplerate * click_duration)

        if click_samples >= interval_samples:
            raise ValueError("Click duration too long for click rate")

        chunk = np.zeros(self.blocksize, dtype=np.float32)
        for i in range(self.phase, self.blocksize, interval_samples):
            if i + click_samples >= self.blocksize:
                break
            if polarity == ClickPolarity.POSITIVE:
                chunk[i:i + click_samples] += click_amplitude
            elif polarity == ClickPolarity.BIPHASIC:
                half = click_samples // 2
                chunk[i:i + half] += click_amplitude
                chunk[i + half:i + click_samples] -= click_amplitude

        self.phase = (self.phase + self.blocksize) % interval_samples

        if self.channels > 1:
            chunk = np.tile(chunk[:, None], (1, self.channels))

        return chunk
    
    def _next_chunk(self) -> NDArray:

        current_stim = self.shared_audio_parameters.stim_select.value

        if current_stim == Stim.SILENCE:
            self.chunk_function = self._silence
        elif current_stim == Stim.PURE_TONE:
            self.chunk_function = self._pure_tone
        elif current_stim == Stim.FREQUENCY_RAMP:
            self.chunk_function = self._frequency_sweep
        elif current_stim == Stim.WHITE_NOISE:
            self.chunk_function = self._white_noise
        elif current_stim == Stim.PINK_NOISE:
            self.chunk_function = self._pink_noise
        elif current_stim == Stim.CLICK_TRAIN:
            self.chunk_function = self._click_train

        return self.chunk_function()

    def run(self):
        while not self.stop_event.is_set():
            chunk = self._next_chunk()
            self.audio_queue.put(chunk)
        
class AudioConsumer(Process):

    def __init__(
            self, 
            audio_queue: Queue, 
            stop_event: EventType,
            samplerate: int = 44100,
            blocksize: int = 1024,
            channels: int = 1
        ):

        super().__init__()

        self.audio_queue = audio_queue
        self.stop_event = stop_event
        self.samplerate = samplerate
        self.blocksize = blocksize 
        self.channels = channels

    def audio_callback(
            self,
            outdata: NDArray,
            frames: int,
            time: Any,
            status: sd.CallbackFlags
        ) -> None:
        
        if status:
            print(status)

        try:
            chunk = self.audio_queue.get_nowait()
        except queue.Empty:
            outdata.fill(0)
        else:
            outdata[:] = chunk

    def run(self):

        with sd.OutputStream(
                callback = self.audio_callback,
                samplerate = self.samplerate,
                blocksize = self.blocksize,
                channels = self.channels,
                dtype = 'float32'
            ):

            while not self.stop_event.is_set():
                time.sleep(0.1)  

class AudioStimWorker(WorkerNode):

    def __init__(
            self,
            units_per_dB_RMS: float = 1,
            samplerate: int = 44100,
            blocksize: int = 1024,
            channels: int = 1,
            timings_file: str = 'audio.csv', 
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)

        self.units_per_dB_RMS = units_per_dB_RMS
        self.samplerate = samplerate
        self.timings_file = timings_file
        self.blocksize = blocksize
        self.channels = channels    

        self.stop_event = Event()
        self.audio_queue = Queue()
        self.shared_audio_parameters = SharedAudioParameters()
        self.audio_producer = AudioProducer(
            audio_queue = self.audio_queue,
            stop_event = self.stop_event,
            shared_audio_parameters = self.shared_audio_parameters,
            samplerate = self.samplerate,
            blocksize = self.blocksize,
            channels = self.channels
        )
        self.audio_consumer = AudioConsumer(
            audio_queue = self.audio_queue,
            stop_event = self.stop_event,
            samplerate = self.samplerate,
            blocksize = self.blocksize,
            channels = self.channels
        )

    def set_filename(self, filename:str):
        self.timings_file = filename

    def initialize(self) -> None:

        prefix, ext = os.path.splitext(self.timings_file)
        timings_file = prefix + time.strftime('_%a_%d_%b_%Y_%Hh%Mmin%Ssec') + ext
        while os.path.exists(timings_file):
            time.sleep(1)
            timings_file = prefix + time.strftime('_%a_%d_%b_%Y_%Hh%Mmin%Ssec') + ext

        self.fd = open(timings_file, 'w')
        headers = (
            'timestamp',
            'time_sec',
            'stim_id',          
            'start_time_sec',
            'phototaxis_polarity',
        )
        self.fd.write(','.join(headers) + '\n')

        self.audio_consumer.start()
        self.audio_producer.start()

        super().initialize()

    def cleanup(self) -> None:

        super().cleanup()
        
        self.stop_event.set()
        self.audio_consumer.join()
        self.audio_producer.join()
        self.fd.close()

    def process_data(self, data: Any) -> None:
        # could be used to do something with fish position
        pass
    
    def process_metadata(self, metadata) -> None:
        # this runs in the worker process
        
        control: Dict = metadata['stim_control']
        
        if control is None:
            return

        self.shared_audio_parameters.from_dict(control)
