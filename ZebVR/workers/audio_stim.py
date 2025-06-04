from dagline import WorkerNode
import matplotlib.pyplot as plt
from scipy.signal import spectrogram, welch
from multiprocessing import RawValue, Process, Queue, Event
from multiprocessing.synchronize  import Event as EventType
import queue
from ZebVR.protocol import DEFAULT, Stim
from typing import Dict, Generator, Optional, Any
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

def pure_tone_coroutine(
        samplerate: int = 44100,
        blocksize: int = 1024,
        frequency: float = 440.0,
        amplitude: float = 0.1,
        channels: int = 1
    ) -> Generator[NDArray, Optional[Dict], None]:
        
    phase = 0.0

    while True:
        t = (np.arange(blocksize) + phase) / samplerate
        chunk = amplitude * np.sin(2 * np.pi * frequency * t)
        if channels > 1:
            chunk = np.tile(chunk[:, None], (1, channels))

        phase += blocksize

        update = yield chunk
        if update:
            frequency = update.get("frequency", frequency)
            amplitude = update.get("amplitude", amplitude)

def frequency_sweep_coroutine(
        samplerate: int = 44100,
        blocksize: int = 1024,
        f_start: float = 440.0,
        f_stop: float = 880.0,
        amplitude: float = 0.1,
        method: str = "linear",
        channels: int = 1,
    ) -> Generator[NDArray, Optional[Dict], None]:
        
    phase = 0.0

    while True:
        t = np.arange(blocksize + phase) / samplerate

        if method == "linear":
            phase_array = 2 * np.pi * (f_start * t + (f_stop - f_start) / 2 * t**2)

        elif method == "log":
            if f_start <= 0 or f_stop <= 0:
                raise ValueError("Log sweep requires positive frequencies")
            k = np.log(f_stop / f_start)
            phase_array = 2 * np.pi * f_start * (np.exp(k * t) - 1) / k

        else:
            raise ValueError("Unsupported method. Choose 'linear' or 'log'.")

        chunk = amplitude * np.sin(phase_array)
        if channels > 1:
            chunk = np.tile(chunk[:, None], (1, channels))

        phase += blocksize

        update = yield chunk
        if update:
            f_start = update.get("f_start", f_start)
            f_stop = update.get("f_stop", f_stop)
            amplitude = update.get("amplitude", amplitude)
            method = update.get("method", method)

def white_noise_coroutine(
        blocksize: int = 1024,
        amplitude: float = 0.1,
        channels: int = 1,
    ) -> Generator[NDArray, Optional[Dict], None]:
        
    while True:
        chunk = amplitude * np.random.randn(blocksize).astype(np.float32)
        if channels > 1:
            chunk = np.tile(chunk[:, None], (1, channels))

        update = yield chunk
        if update:
            amplitude = update.get("amplitude", amplitude)

def pink_noise_coroutine(
        blocksize: int = 1024,
        amplitude: float = 0.1,
        channels: int = 1,
    ) -> Generator[NDArray, Optional[Dict], None]:
        
    while True:
        # Voss-McCartney algorithm approximation
        white = np.random.randn(blocksize).astype(np.float32)
        b = [0.99765, 0.96300, 0.57000]
        a = [0.0990460, 0.2965164, 1.0526913]
        y = np.zeros_like(white)
        x0, x1, x2 = 0.0, 0.0, 0.0
        for i in range(blocksize):
            x = white[i]
            x0 = b[0] * x + a[0] * x0
            x1 = b[1] * x + a[1] * x1
            x2 = b[2] * x + a[2] * x2
            y[i] = x0 + x1 + x2 + x * 0.1848

        chunk = (amplitude * y / np.max(np.abs(y)))
        if channels > 1:
            chunk = np.tile(chunk[:, None], (1, channels))

        update = yield chunk
        if update:
            amplitude = update.get("amplitude", amplitude)

def click_train_coroutine(
        samplerate: int = 44100,
        blocksize: int = 1024,
        click_rate: float = 10.0,
        click_amplitude: float = 0.5,
        click_duration: float = 0.001,
        polarity: str = "biphasic",
        channels: int = 1,
    ) -> Generator[NDArray, Optional[Dict], None]:
        
    phase = 0
    interval_samples = int(samplerate / click_rate)
    click_samples = int(samplerate * click_duration)

    if click_samples >= interval_samples:
        raise ValueError("Click duration too long for click rate")

    while True:
        chunk = np.zeros(blocksize, dtype=np.float32)
        for i in range(phase, blocksize, interval_samples):
            if i + click_samples >= blocksize:
                break
            if polarity == "positive":
                chunk[i:i + click_samples] += click_amplitude
            elif polarity == "biphasic":
                half = click_samples // 2
                chunk[i:i + half] += click_amplitude
                chunk[i + half:i + click_samples] -= click_amplitude

        phase = (phase + blocksize) % interval_samples
        if channels > 1:
            chunk = np.tile(chunk[:, None], (1, channels))

        update = yield chunk
        if update:
            click_rate = update.get("click_rate", click_rate)
            click_amplitude = update.get("click_amplitude", click_amplitude)
            click_duration = update.get("click_duration", click_duration)
            polarity = update.get("polarity", polarity)
            interval_samples = int(samplerate / click_rate)
            click_samples = int(samplerate * click_duration)

def silence_coroutine(
        blocksize: int = 1024,
        channels: int = 1,
    ) -> Generator[NDArray, Optional[Dict], None]:

    chunk = np.zeros((blocksize, channels), dtype=np.float32)

    while True:
        update = yield chunk

class SharedAudioParameters:

    def __init__(self):
        
        self.start_time_sec = RawValue('d', 0) 
        self.stim_select = RawValue('d', Stim.DARK) 
        self.phototaxis_polarity = RawValue('d', DEFAULT['phototaxis_polarity']) 

    def from_dict(self, d: Dict) -> None:

        self.start_time_sec.value = d.get('time_sec', 0)
        self.stim_select.value = d.get('stim_select', Stim.DARK)
        self.phototaxis_polarity.value = d.get('phototaxis_polarity', DEFAULT['phototaxis_polarity'])

    def to_dict(self) -> Dict:
        
        parameters = {}
        return parameters

class AudioProducer(Process):
    
    def __init__(
            self, 
            audio_queue: Queue, 
            stop_event: EventType,
            samplerate: int = 44100,
            blocksize: int = 1024,
            channels: int = 1
        ):

        self.stop_event = stop_event
        self.audio_queue = audio_queue
        self.samplerate = samplerate
        self.blocksize = blocksize 
        self.channels = channels

        self.shared_audio_parameters = None 
        self.stim_coroutine = {
            Stim.PURE_TONE: pure_tone_coroutine(
                samplerate = self.samplerate,
                blocksize = self.blocksize,
                channels = self.channels,
            ),
            Stim.NOISE: white_noise_coroutine(
                blocksize = self.blocksize,
                channels = self.channels,
            ),
            Stim.FREQUENCY_RAMP: frequency_sweep_coroutine(
                samplerate = self.samplerate,
                blocksize = self.blocksize,
                channels = self.channels,
            ),
            Stim.CLICK_TRAIN: click_train_coroutine(
                samplerate = self.samplerate,
                blocksize = self.blocksize,
                channels = self.channels,
            ),
            Stim.SILENCE: silence_coroutine(
                blocksize = self.blocksize,
                channels = self.channels,
            ),
        }

    def set_shared_parameters(self, shared_audio_parameters: SharedAudioParameters):
        self.shared_audio_parameters = shared_audio_parameters

    def run(self):
        if self.shared_audio_parameters is None:
            raise ValueError("SharedAudioParameters must be set before running the producer")
        
        while not self.stop_event.is_set():
            current_stim = self.shared_audio_parameters.stim_select.value
            coroutine = self.stim_coroutine.get(current_stim, Stim.SILENCE)
            chunk = coroutine.send(self.shared_audio_parameters.to_dict())
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
            audio_producer: AudioProducer,
            audio_consumer: AudioConsumer,
            samplerate: int = 44100, 
            timings_file: str = 'audio.csv', 
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)

        self.samplerate = samplerate
        self.timings_file = timings_file
        self.audio_producer = audio_producer
        self.audio_consumer = audio_consumer 

        self.shared_audio_parameters = SharedAudioParameters()
        self.audio_producer.set_shared_parameters(self.shared_audio_parameters)

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

        self.audio_consumer.join()
        self.audio_producer.join()
        self.fd.close()

    def process_data(self, data: Any) -> None:
        # could be used to do something with fish position
        pass
    
    def process_metadata(self, metadata) -> None:
        # this runs in the worker process
        
        control: Dict = metadata['audio_stim_control']
        
        if control is None:
            return
        
        timestamp = time.perf_counter_ns()
        timestamp_sec = 1e-9*timestamp
        control['time_sec'] = timestamp_sec

        self.shared_audio_parameters.from_dict(control)
