from typing import Tuple, Any
from dagline import WorkerNode
from multiprocessing import Process
from numpy.typing import NDArray
import numpy as np 
import sounddevice as sd

def pure_tone(
    frequency: float,
    duration: float,
    samplerate: int = 44100,
    amplitude: float = 0.1,
    fade_ms: float = 5.0,
) -> NDArray:
    """
    Generate a sine wave tone with optional cosine-squared onset/offset ramps.

    Parameters:
        frequency (float): Frequency of the tone in Hz.
        duration (float): Duration in seconds.
        samplerate (int): Sampling rate in Hz.
        amplitude (float): Peak amplitude (0 to 1).
        fade_ms (float): Duration of fade-in and fade-out in milliseconds.

    Returns:
        np.ndarray: Audio waveform with shape (n_samples,)
    """
    t = np.linspace(0, duration, int(samplerate * duration), endpoint=False)
    tone = amplitude * np.sin(2 * np.pi * frequency * t)

    fade_samples = int(samplerate * fade_ms / 1000)
    if fade_samples * 2 >= len(tone):
        raise ValueError("Fade duration too long for tone length")

    envelope = np.ones_like(tone)
    fade_in = np.sin(np.linspace(0, np.pi / 2, fade_samples))**2
    fade_out = np.sin(np.linspace(np.pi / 2, 0, fade_samples))**2
    envelope[:fade_samples] = fade_in
    envelope[-fade_samples:] = fade_out

    return tone * envelope

def frequency_sweep(
    f_start: float,
    f_stop: float,
    duration: float,
    samplerate: int = 44100,
    amplitude: float = 0.1,
    fade_ms: float = 5.0,
    method: str = 'linear',
) -> NDArray:
    """
    Generate a frequency sweep (chirp) with cosine-squared fade-in/out.

    Parameters:
        f_start (float): Start frequency in Hz.
        f_stop (float): End frequency in Hz.
        duration (float): Duration in seconds.
        samplerate (int): Sampling rate in Hz.
        amplitude (float): Peak amplitude.
        fade_ms (float): Duration of fade-in/out in milliseconds.
        method (str): 'linear' or 'log' sweep.

    Returns:
        np.ndarray: Sweep waveform.
    """
    t = np.linspace(0, duration, int(samplerate * duration), endpoint=False)

    if method == 'linear':
        # Linear frequency sweep
        phase = 2 * np.pi * (f_start * t + (f_stop - f_start) / (2 * duration) * t**2)
    elif method == 'log':
        if f_start <= 0 or f_stop <= 0:
            raise ValueError("Log sweep requires positive frequencies")
        k = np.log(f_stop / f_start) / duration
        phase = 2 * np.pi * f_start * (np.exp(k * t) - 1) / k
    else:
        raise ValueError("Unsupported method. Choose 'linear' or 'log'.")

    sweep = amplitude * np.sin(phase)

    # Apply cos² fade
    fade_samples = int(samplerate * fade_ms / 1000)
    if fade_samples * 2 >= len(sweep):
        raise ValueError("Fade duration too long for sweep length")

    envelope = np.ones_like(sweep)
    fade_in = np.sin(np.linspace(0, np.pi / 2, fade_samples))**2
    fade_out = np.sin(np.linspace(np.pi / 2, 0, fade_samples))**2
    envelope[:fade_samples] = fade_in
    envelope[-fade_samples:] = fade_out

    return sweep * envelope

import numpy as np

def band_limited_white_noise(
    f_low: float,
    f_high: float,
    duration: float,
    samplerate: int = 44100,
    amplitude: float = 0.1,
    fade_ms: float = 5.0
) -> NDArray:
    """
    Generate white noise limited to a specific frequency band with cos² fades.

    Parameters:
        f_low (float): Lower cutoff frequency in Hz.
        f_high (float): Upper cutoff frequency in Hz.
        duration (float): Duration of the noise in seconds.
        samplerate (int): Sampling rate in Hz.
        amplitude (float): Peak amplitude (approximate).
        fade_ms (float): Duration of fade-in/out in milliseconds.

    Returns:
        np.ndarray: Band-limited noise waveform.
    """
    n_samples = int(duration * samplerate)
    noise = np.random.normal(0, 1, n_samples)

    # Apply FFT bandpass filter
    freqs = np.fft.rfftfreq(n_samples, d=1/samplerate)
    fft_noise = np.fft.rfft(noise)

    # Zero out frequencies outside the desired band
    band_mask = (freqs >= f_low) & (freqs <= f_high)
    fft_noise[~band_mask] = 0

    # Convert back to time domain
    filtered_noise = np.fft.irfft(fft_noise, n=n_samples)

    # Normalize to target amplitude
    filtered_noise *= amplitude / np.max(np.abs(filtered_noise) + 1e-12)

    # Apply cos² fade-in/out
    fade_samples = int(samplerate * fade_ms / 1000)
    if fade_samples * 2 >= n_samples:
        raise ValueError("Fade duration too long for noise length")

    envelope = np.ones(n_samples)
    fade_in = np.sin(np.linspace(0, np.pi / 2, fade_samples))**2
    fade_out = np.sin(np.linspace(np.pi / 2, 0, fade_samples))**2
    envelope[:fade_samples] = fade_in
    envelope[-fade_samples:] = fade_out

    return filtered_noise * envelope

def band_limited_pink_noise(
    f_low: float,
    f_high: float,
    duration: float,
    samplerate: int = 44100,
    amplitude: float = 0.1,
    fade_ms: float = 5.0
) -> NDArray:
    """
    Generate pink noise limited to a specific frequency band with cos² fades.

    Parameters:
        f_low (float): Lower cutoff frequency in Hz.
        f_high (float): Upper cutoff frequency in Hz.
        duration (float): Duration of the noise in seconds.
        samplerate (int): Sampling rate in Hz.
        amplitude (float): Peak amplitude (approximate).
        fade_ms (float): Duration of fade-in/out in milliseconds.

    Returns:
        np.ndarray: Band-limited pink noise waveform.
    """
    n_samples = int(duration * samplerate)

    # Generate white noise in frequency domain
    freqs = np.fft.rfftfreq(n_samples, d=1/samplerate)
    n_freqs = len(freqs)

    # Create pink spectrum: scale ~ 1/f (avoid divide-by-zero at DC)
    pink_spectrum = np.random.normal(0, 1, n_freqs) + 1j * np.random.normal(0, 1, n_freqs)
    pink_spectrum /= np.sqrt(np.maximum(freqs, 1e-6))  # 1/sqrt(f) gives 1/f power

    # Apply bandpass mask
    band_mask = (freqs >= f_low) & (freqs <= f_high)
    pink_spectrum[~band_mask] = 0

    # Inverse FFT to get time domain signal
    pink_noise = np.fft.irfft(pink_spectrum, n=n_samples)

    # Normalize
    pink_noise *= amplitude / np.max(np.abs(pink_noise) + 1e-12)

    # Cos² fade
    fade_samples = int(samplerate * fade_ms / 1000)
    if fade_samples * 2 >= n_samples:
        raise ValueError("Fade duration too long for noise length")

    envelope = np.ones(n_samples)
    fade_in = np.sin(np.linspace(0, np.pi / 2, fade_samples))**2
    fade_out = np.sin(np.linspace(np.pi / 2, 0, fade_samples))**2
    envelope[:fade_samples] = fade_in
    envelope[-fade_samples:] = fade_out

    return pink_noise * envelope


class VisualStimWorker(WorkerNode):

    def __init__(self, stim: VisualStim, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stim = stim
        self.display_process = None

    def run(self) -> None:
        self.stim.initialize()
        # TODO set flag here
        while not self.stop_event.is_set():
            app.process_events()
        self.stim.cleanup()
        app.quit()

    def set_filename(self, filename:str):
        self.stim.set_filename(filename)

    def initialize(self) -> None:
        super().initialize()
        # launch main window loop in a separate process 
        self.display_process = Process(target=self.run)
        self.display_process.start()
        self.stim.initialized.wait()

    def cleanup(self) -> None:
        super().cleanup()
        self.display_process.join()

    def process_data(self, data: Any) -> None:
        return self.stim.process_data(data)
    
    def process_metadata(self, metadata) -> Any:
        return self.stim.process_metadata(metadata)