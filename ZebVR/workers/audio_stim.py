from dagline import WorkerNode
import matplotlib.pyplot as plt
from scipy.signal import spectrogram, welch
from multiprocessing import RawValue, Process, Queue, Event
from multiprocessing.synchronize  import Event as EventType
import queue
from ZebVR.protocol import DEFAULT, Stim, ClickPolarity, RampType
from typing import Dict, Any
import time
import os
import sounddevice as sd
import numpy as np
from numpy.typing import NDArray


# debug ramps 
def linear_sweep(f_start, f_end, duration, sample_rate):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    k = (f_end - f_start) / duration
    phase = 2 * np.pi * (f_start * t + 0.5 * k * t**2)
    return np.sin(phase)

def log_sweep(f_start, f_end, duration, sample_rate):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    beta = np.log(f_end / f_start)
    phase = 2 * np.pi * f_start * duration / beta * (np.exp(beta * t / duration) - 1)
    return np.sin(phase)

def powerlaw_sweep(f_start, f_end, duration, sample_rate, exponent=2):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    delta_f = f_end - f_start
    phase = 2 * np.pi * (
        f_start * t + (delta_f / (exponent + 1)) * (t ** (exponent + 1)) / (duration ** exponent)
    )
    return np.sin(phase)
# - debug ramps


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

    plt.show(block=False)

class SharedAudioParameters:

    def __init__(self):
        
        self.stim_select = RawValue('d', Stim.SILENCE)
        self.frequency_Hz = RawValue('d', DEFAULT['frequency_Hz'])
        self.amplitude_dB = RawValue('d', DEFAULT['amplitude_dB'])
        self.ramp_start_Hz = RawValue('d', DEFAULT['audio_ramp_start_Hz'])
        self.ramp_stop_Hz = RawValue('d', DEFAULT['audio_ramp_stop_Hz'])
        self.ramp_duration_sec = RawValue('d', DEFAULT['audio_ramp_duration_sec'])
        self.ramp_powerlaw_exponent = RawValue('d', DEFAULT['audio_ramp_powerlaw_exponent'])
        self.ramp_type = RawValue('d', DEFAULT['audio_ramp_type'])
        self.click_rate = RawValue('d', DEFAULT['click_rate'])
        self.click_duration = RawValue('d', DEFAULT['click_duration'])
        self.click_polarity = RawValue('d', DEFAULT['click_polarity'])

    def from_dict(self, d: Dict) -> None:

        self.stim_select.value = d.get('stim_select', Stim.SILENCE)
        self.frequency_Hz.value = d.get('frequency_Hz', DEFAULT['frequency_Hz'])
        self.amplitude_dB.value = d.get('amplitude_dB', DEFAULT['amplitude_dB'])
        self.ramp_start_Hz.value = d.get('ramp_start_Hz', DEFAULT['audio_ramp_start_Hz'])
        self.ramp_stop_Hz.value = d.get('ramp_stop_Hz', DEFAULT['audio_ramp_stop_Hz'])
        self.ramp_duration_sec.value = d.get('ramp_duration_sec', DEFAULT['audio_ramp_duration_sec'])
        self.ramp_powerlaw_exponent.value = d.get('ramp_powerlaw_exponent', DEFAULT['audio_ramp_powerlaw_exponent'])
        self.ramp_type.value = d.get('ramp_type', DEFAULT['audio_ramp_type'])
        self.click_rate.value = d.get('click_rate', DEFAULT['click_rate'])
        self.click_duration.value = d.get('click_duration', DEFAULT['click_duration'])
        self.click_polarity = d.get('click_polarity', DEFAULT['click_polarity'])

class AudioProducer(Process):
    
    def __init__(
            self, 
            audio_queue: Queue, 
            stop_event: EventType,
            shared_audio_parameters: SharedAudioParameters,
            samplerate: int = 44100,
            blocksize: int = 1024,
            channels: int = 1,
            rollover_time_sec: float = 3600
        ):

        super().__init__()

        self.stop_event = stop_event
        self.audio_queue = audio_queue
        self.samplerate = samplerate
        self.blocksize = blocksize 
        self.channels = channels
        self.shared_audio_parameters = shared_audio_parameters 
        self.rollover_time_sec = rollover_time_sec

        self.rollover_phase = int(rollover_time_sec * samplerate)
        self.phase: int = 0
        self.chunk_function = self._silence

    def _silence(self) -> NDArray:
        return np.zeros((self.blocksize,), dtype=np.float32)
    
    def _pure_tone(self) -> NDArray:
        frequency = self.shared_audio_parameters.frequency_Hz.value
        t = (np.arange(self.blocksize) + self.phase) / self.samplerate
        return np.sin(2 * np.pi * frequency * t)

    def _frequency_ramp(self) -> NDArray:
        f_start = self.shared_audio_parameters.ramp_start_Hz.value
        f_stop = self.shared_audio_parameters.ramp_stop_Hz.value
        ramp_duration = self.shared_audio_parameters.ramp_duration_sec.value
        exponent = self.shared_audio_parameters.ramp_powerlaw_exponent.value
        method = RampType(self.shared_audio_parameters.ramp_type.value) 

        t = np.arange(self.blocksize + self.phase) / self.samplerate

        if method == RampType.LINEAR:
            k = (f_stop - f_start) / ramp_duration
            phase_array = 2 * np.pi * (f_start * t + k/2 * t**2)

        elif method == RampType.LOG:
            k = np.log(f_stop / f_start)
            phase_array = 2 * np.pi * f_start * ramp_duration / k * (np.exp(k * t / ramp_duration) - 1)

        elif method == RampType.POWER_LAW:
            delta_f = f_stop - f_start
            phase_array = 2 * np.pi * (
                f_start * t + (delta_f / (exponent + 1)) * (t ** (exponent + 1)) / (ramp_duration ** exponent)
            )

        else:
            raise ValueError("Unsupported method. Choose 'linear', 'log' or 'power law'.")
        
        return np.sin(phase_array)

    def _white_noise(self) -> NDArray:
        return np.random.randn(self.blocksize).astype(np.float32)
    
    def _pink_noise(self) -> NDArray:
        # pink noise approximation using Paul Kellet's economy filter
        # https://www.firstpr.com.au/dsp/pink-noise/#Filtering
        # Optimized for a 44100Hz samplerate

        white = np.random.randn(self.blocksize).astype(np.float32)
        pink = np.zeros_like(white)
        x0, x1, x2 = 0.0, 0.0, 0.0
        for i in range(self.blocksize):
            x0 = 0.99765 * x0 + white[i] * 0.0990460
            x1 = 0.96300 * x1 + white[i] * 0.2965164
            x2 = 0.57000 * x2 + white[i] * 1.0526913
            pink[i] = x0 + x1 + x2 + white[i] * 0.1848
        return pink
    
    def _click_train(self) -> NDArray:

        click_rate = self.shared_audio_parameters.click_rate.value
        click_duration = self.shared_audio_parameters.click_duration.value
        polarity = ClickPolarity(self.shared_audio_parameters.click_polarity.value)

        interval_samples = int(self.samplerate / click_rate)
        click_samples = int(self.samplerate * click_duration)

        if click_samples >= interval_samples:
            raise ValueError("Click duration too long for click rate")

        chunk = np.zeros(self.blocksize, dtype=np.float32)
        for i in range(self.phase, self.blocksize, interval_samples):
            if i + click_samples >= self.blocksize:
                break
            if polarity == ClickPolarity.POSITIVE:
                chunk[i:i + click_samples] += 1
            elif polarity == ClickPolarity.BIPHASIC:
                half = click_samples // 2
                chunk[i:i + half] += 1
                chunk[i + half:i + click_samples] -= 1
        return chunk
    
    def _next_chunk(self) -> NDArray:

        current_stim = self.shared_audio_parameters.stim_select.value
        amplitude = self.shared_audio_parameters.amplitude_dB.value

        if current_stim == Stim.SILENCE:
            self.chunk_function = self._silence
        elif current_stim == Stim.PURE_TONE:
            self.chunk_function = self._pure_tone
        elif current_stim == Stim.FREQUENCY_RAMP:
            self.chunk_function = self._frequency_ramp
        elif current_stim == Stim.WHITE_NOISE:
            self.chunk_function = self._white_noise
        elif current_stim == Stim.PINK_NOISE:
            self.chunk_function = self._pink_noise
        elif current_stim == Stim.CLICK_TRAIN:
            self.chunk_function = self._click_train
        else:
            self.chunk_function = self._silence

        chunk = amplitude * self.chunk_function()
        chunk = np.tile(chunk[:, None], (1, self.channels))
        self.phase = (self.phase + self.blocksize) % self.rollover_phase
        return chunk

    def run(self):

        while not self.stop_event.is_set():
            chunk = self._next_chunk()
            self.audio_queue.put(chunk)
            time.sleep(self.blocksize/self.samplerate) # maybe a bit less?
        
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
            callback_time: Any,
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
            units_per_dB: float = 1,
            samplerate: int = 44100,
            blocksize: int = 1024,
            channels: int = 1,
            timings_file: str = 'audio.csv', 
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)

        self.units_per_dB = units_per_dB
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

if __name__ == '__main__':

    q = Queue()
    s = Event()
    params = SharedAudioParameters()
    consumer = AudioConsumer(q,s)
    producer = AudioProducer(q,s,params)
    consumer.start()
    producer.start()

    params.stim_select.value = Stim.PURE_TONE
    params.amplitude_dB.value = 1
    params.frequency_Hz.value = 440
    
    time.sleep(10)
    s.set()
    producer.join()
    consumer.join()