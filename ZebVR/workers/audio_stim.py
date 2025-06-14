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
import matplotlib.pyplot as plt
from numba import njit
import av
from ZebVR.utils import SharedString

# TODO barrier to check everyone up and running
# TODO log timings 

# For pink noise generation see:
# Voss-McCartney method: https://www.firstpr.com.au/dsp/pink-noise/voss-mccartney/
# IIR filter bank: http://www.cooperbaker.com/home/code/pink%20noise/

@njit
def voss_mccartney(n_samples, n_layers=16):
    """Voss-McCartney pink noise generator."""
    out = np.zeros(n_samples)
    layers = np.zeros(n_layers)
    counters = np.zeros(n_layers, dtype=np.int32)
    rand = np.random.normal

    for i in range(n_samples):
        for j in range(n_layers):
            if counters[j] == 0:
                layers[j] = rand()
                counters[j] = 2 ** j
            counters[j] -= 1
        out[i] = layers.sum()
    return out

def audio_file_generator(filename, samplerate, channels, blocksize):
    """
    Generator that yields fixed-size blocks of decoded and resampled audio samples from a file.

    Parameters:
        filename (str): Path to the input audio or video file.
        samplerate (int): Desired output sample rate (in Hz).
        channels (int): Desired number of output audio channels (e.g., 1 for mono, 2 for stereo).
        blocksize (int): Number of audio samples per block (per channel) to yield.

    Yields:
        np.ndarray: A NumPy array of shape (blocksize, channels) and dtype float32, 
                    containing PCM audio samples in the range [-1.0, 1.0]. 
                    The last block is zero-padded if the file ends mid-block.
    """

    with av.open(filename) as container:

        audio_stream = container.streams.audio[0]
        resampler = av.audio.resampler.AudioResampler(
            format = 'flt',
            layout = av.audio.layout.AudioLayout(channels),
            rate = samplerate
        )

        buffer = np.zeros((0, channels), dtype=np.float32)
        for frame in container.decode(audio_stream):
            for resampled in resampler.resample(frame):
                samples = resampled.to_ndarray().reshape((resampled.samples,-1))
                buffer = np.vstack((buffer, samples))
                
                while buffer.shape[0] >= blocksize:
                    yield buffer[:blocksize, :]
                    buffer = buffer[blocksize:, :]

        # final block
        if buffer.shape[0] > 0:
            final = np.zeros((blocksize, channels), dtype=np.float32)
            final[:buffer.shape[0]] = buffer
            yield final

def plot_waveform_spectrogram_and_psd(
        signal: np.ndarray,
        samplerate: int = 44100,
        max_freq: float = 8000,
        title_prefix: str = "Audio Signal",
        cmap: str = "magma",
        block: bool = False
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

    plt.show(block=block)

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
        self.audio_file_path = SharedString(initializer = DEFAULT['audio_file_path'])

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
        self.click_polarity.value = d.get('click_polarity', DEFAULT['click_polarity'])
        self.audio_file_path.value = d.get('audio_file_path', DEFAULT['audio_file_path'])

class AudioProducer(Process):

    RMS_SINE_NORM = np.sqrt(2)
    
    def __init__(
            self, 
            audio_queue: Queue, 
            stop_event: EventType,
            shared_audio_parameters: SharedAudioParameters,
            samplerate: int = 44100,
            blocksize: int = 256,
            channels: int = 1,
            rollover_time_sec: float = 3600,
            units_per_dB: float = 1/120
        ):

        super().__init__()

        self.audio_stop_event = stop_event
        self.audio_queue = audio_queue
        self.samplerate = samplerate
        self.blocksize = blocksize 
        self.channels = channels
        self.shared_audio_parameters = shared_audio_parameters 
        self.rollover_time_sec = rollover_time_sec
        self.units_per_dB = units_per_dB

        self.rollover_phase = int(rollover_time_sec * samplerate)
        self.phase: int = 0
        self.current_stim: Stim = Stim.SILENCE
        self.chunk_function = self._silence

        # For file-based streaming
        self._file_gen = None
        self._file_name = None

    @staticmethod
    def normalize_rms(signal: NDArray, target_rms: float = 1):
        current_rms = np.sqrt(np.mean(signal**2))
        if current_rms > 0:
            return signal * (target_rms / current_rms)
        return signal

    def _silence(self) -> NDArray:
        return np.zeros((self.blocksize, self.channels), dtype=np.float32)
    
    def _pure_tone(self) -> NDArray:
        frequency = self.shared_audio_parameters.frequency_Hz.value
        t = (np.arange(self.blocksize) + self.phase) / self.samplerate
        chunk = self.RMS_SINE_NORM * np.sin(2 * np.pi * frequency * t)
        chunk = chunk.astype(np.float32)
        chunk = np.tile(chunk[:, None], (1, self.channels))
        return chunk
    
    def _frequency_ramp(self) -> NDArray:
        f_start = self.shared_audio_parameters.ramp_start_Hz.value
        f_stop = self.shared_audio_parameters.ramp_stop_Hz.value
        ramp_duration = self.shared_audio_parameters.ramp_duration_sec.value
        exponent = self.shared_audio_parameters.ramp_powerlaw_exponent.value
        method = RampType(self.shared_audio_parameters.ramp_type.value) 

        t = (np.arange(self.blocksize) + self.phase) / self.samplerate

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
        
        chunk = self.RMS_SINE_NORM * np.sin(phase_array)
        chunk = chunk.astype(np.float32)
        chunk = np.tile(chunk[:, None], (1, self.channels))
        return chunk
    
    def _audio_file(self) -> NDArray:
        # NOTE: probable underrun on file opening
    
        filename = self.shared_audio_parameters.audio_file_path.value
        if filename != self._file_name or self._file_gen is None:
            self._file_name = filename
            self._file_gen = audio_file_generator(filename, self.samplerate, self.channels, self.blocksize)

        try:
            chunk = next(self._file_gen)
        except StopIteration: 
            self._file_gen = audio_file_generator(filename, self.samplerate, self.channels, self.blocksize)
            chunk = next(self._file_gen)

        return chunk

    def _white_noise(self) -> NDArray:
        white = np.random.randn(self.blocksize)
        chunk = self.normalize_rms(white.astype(np.float32))
        chunk = chunk.astype(np.float32)
        chunk = np.tile(chunk[:, None], (1, self.channels))
        return chunk
    
    def _pink_noise(self) -> NDArray:
        pink = voss_mccartney(self.blocksize)
        chunk = self.normalize_rms(pink.astype(np.float32))
        chunk = chunk.astype(np.float32)
        chunk = np.tile(chunk[:, None], (1, self.channels))
        return chunk
    
    def _brown_noise(self) -> NDArray:
        brown = np.cumsum(np.random.randn(self.blocksize))
        chunk = self.normalize_rms(brown.astype(np.float32))
        chunk = chunk.astype(np.float32)
        chunk = np.tile(chunk[:, None], (1, self.channels))
        return chunk
    
    def _click_train(self) -> NDArray:
        # TODO handle block boundaries better

        click_rate = self.shared_audio_parameters.click_rate.value
        click_duration = self.shared_audio_parameters.click_duration.value
        polarity = ClickPolarity(self.shared_audio_parameters.click_polarity.value)

        interval_samples = int(self.samplerate / click_rate)
        click_samples = int(self.samplerate * click_duration)
        if click_samples >= interval_samples:
            return self._silence()

        chunk = np.zeros(self.blocksize, dtype=np.float32)
        first_click = (-self.phase) % interval_samples
        click_times = np.arange(
            first_click,  
            self.blocksize,                
            interval_samples          
        )
        for click_pos in click_times:

            if polarity == ClickPolarity.POSITIVE:
                chunk[click_pos:click_pos + click_samples] += 1

            elif polarity == ClickPolarity.BIPHASIC:
                half = click_samples // 2
                chunk[click_pos:click_pos + half] += 1
                chunk[click_pos + half:click_pos + click_samples] -= 1  
        
        chunk = chunk.astype(np.float32)
        chunk = np.tile(chunk[:, None], (1, self.channels))
        return chunk
    
    def _next_chunk(self) -> NDArray:

        amplitude_dB = self.shared_audio_parameters.amplitude_dB.value

        if self.shared_audio_parameters.stim_select.value != self.current_stim:
            self.phase = 0
            self.current_stim = self.shared_audio_parameters.stim_select.value

        if self.current_stim == Stim.SILENCE:
            self.chunk_function = self._silence
        elif self.current_stim == Stim.PURE_TONE:
            self.chunk_function = self._pure_tone
        elif self.current_stim == Stim.FREQUENCY_RAMP:
            self.chunk_function = self._frequency_ramp
        elif self.current_stim == Stim.WHITE_NOISE:
            self.chunk_function = self._white_noise
        elif self.current_stim == Stim.PINK_NOISE:
            self.chunk_function = self._pink_noise
        elif self.current_stim == Stim.BROWN_NOISE:
            self.chunk_function = self._brown_noise
        elif self.current_stim == Stim.CLICK_TRAIN:
            self.chunk_function = self._click_train
        elif self.current_stim == Stim.AUDIO_FILE:
            self.chunk_function = self._audio_file
        else:
            self.chunk_function = self._silence

        chunk = self.chunk_function()
        chunk = amplitude_dB * self.units_per_dB * chunk
        self.phase = (self.phase + self.blocksize) % self.rollover_phase

        return chunk

    def run(self):

        voss_mccartney(self.blocksize)  # warm up the JIT compiler

        while not self.audio_stop_event.is_set():
            chunk = self._next_chunk()
            self.audio_queue.put(chunk, block=True)

class AudioConsumer(Process):

    def __init__(
            self, 
            audio_queue: Queue, 
            stop_event: EventType,
            device_index: int,
            samplerate: int = 44100,
            blocksize: int = 256,
            channels: int = 1
        ):

        super().__init__()

        self.audio_queue = audio_queue
        self.audio_stop_event = stop_event
        self.device_index = device_index
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
            # print(f'rms: {np.sqrt(np.mean(chunk**2))}')
        except queue.Empty:
            print('audio underrun')
            outdata.fill(0)
        else:
            outdata[:] = chunk       

    def run(self):

        import sounddevice as sd 
        sd.default.device = None, self.device_index
        sd.default.samplerate = self.samplerate
        sd.default.channels = None, self.channels
        sd.default.dtype = None, 'float32'
        sd.default.latency = None, 'low'

        with sd.OutputStream(
                callback = self.audio_callback,
                samplerate = self.samplerate,
                blocksize = self.blocksize,
                channels = self.channels,
                dtype = 'float32'
            ):

            while not self.audio_stop_event.is_set():
                time.sleep(0.1)  

class AudioStimWorker(WorkerNode):

    def __init__(
            self,
            device_index: int = 0,
            units_per_dB: float = 1/120,
            samplerate: int = 44100,
            blocksize: int = 256,
            channels: int = 1,
            timings_file: str = 'audio.csv',
            rollover_time_sec: float = 3600,  
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)

        self.units_per_dB = units_per_dB
        self.device_index = device_index
        self.rollover_time_sec = rollover_time_sec
        self.samplerate = samplerate
        self.timings_file = timings_file
        self.blocksize = blocksize
        self.channels = channels    

        self.audio_stop_event = Event() 
        self.audio_queue = Queue(maxsize=2)
        self.shared_audio_parameters = SharedAudioParameters()

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

        self.audio_producer = AudioProducer(
            audio_queue = self.audio_queue,
            stop_event = self.audio_stop_event,
            shared_audio_parameters = self.shared_audio_parameters,
            samplerate = self.samplerate,
            blocksize = self.blocksize,
            channels = self.channels,
            rollover_time_sec = self.rollover_time_sec,
            units_per_dB  = self.units_per_dB
        )
        self.audio_consumer = AudioConsumer(
            audio_queue = self.audio_queue,
            stop_event = self.audio_stop_event,
            device_index = self.device_index,
            samplerate = self.samplerate,
            blocksize = self.blocksize,
            channels = self.channels
        )
    
        self.audio_consumer.start()
        self.audio_producer.start()

        super().initialize()

    def cleanup(self) -> None:

        super().cleanup() # should this go at the end?
        
        self.audio_stop_event.set()

        # make sure queue is empty before joining
        time.sleep(0.5)
        try:
            while True:
                self.audio_queue.get_nowait()
        except queue.Empty:
            pass

        self.audio_consumer.join()
        self.audio_producer.join()
        self.fd.close()

    def process_data(self, data: Any) -> None:
        # could be used to do something with fish position
        pass
    
    def process_metadata(self, metadata) -> None:
        # this runs in the worker process
        
        control: Dict = metadata.get('audio_stim_control', None)
        if control is None:
            return

        # TODO add time to the parameters and use that to reset the phase
        # that way, specifying the same stimulus again also resets the phase

        self.shared_audio_parameters.from_dict(control)

        # Write to file here? Log only if there is a change?
        # implement the logic in SharedAudioParameters?

def clear_queue(q: Queue) -> None:
    try:
        while True:
            q.get_nowait()
    except queue.Empty:
        pass

if __name__ == '__main__':

    q = Queue(maxsize=2) # double-buffering
    s = Event()
    channels = 2
    blocksize = 256
    samplerate = 44100
    params = SharedAudioParameters()
    consumer = AudioConsumer(q,s,channels=channels, device_index=4, blocksize=blocksize, samplerate=samplerate)
    producer = AudioProducer(q,s,params,channels=channels, blocksize=blocksize, samplerate=samplerate)
    consumer.start()
    producer.start()

    params.amplitude_dB.value = 10

    print("pure tone")
    params.stim_select.value = Stim.PURE_TONE
    params.frequency_Hz.value = 440
    time.sleep(5)

    print("frequency ramp")
    params.stim_select.value = Stim.FREQUENCY_RAMP
    params.ramp_type.value = RampType.LOG
    params.ramp_powerlaw_exponent = 1.67
    params.ramp_start_Hz.value = 440
    params.ramp_stop_Hz.value = 880
    params.ramp_duration_sec.value = 2.5
    time.sleep(2.5)

    print("pink noise")
    params.stim_select.value = Stim.PINK_NOISE
    time.sleep(5)
    
    print("white noise")
    params.stim_select.value = Stim.WHITE_NOISE
    time.sleep(5)

    print("brown noise")
    params.stim_select.value = Stim.BROWN_NOISE
    time.sleep(5)

    print("silence")
    params.stim_select.value = Stim.SILENCE
    time.sleep(5)

    print("clicks")
    params.stim_select.value = Stim.CLICK_TRAIN
    params.click_rate.value = 20
    params.click_duration.value = 0.001
    params.click_polarity.value = ClickPolarity.BIPHASIC
    time.sleep(5)

    print("audio file")
    params.amplitude_dB.value = 120
    params.stim_select.value = Stim.AUDIO_FILE
    time.sleep(6)

    s.set()
    clear_queue(q)
    producer.join()
    consumer.join()
