from typing import Tuple, Any
from dagline import WorkerNode
from multiprocessing import Process
from numpy.typing import NDArray
import numpy as np 
import sounddevice as sd
import matplotlib.pyplot as plt
from scipy.signal import spectrogram, welch

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

def click_train(
    samplerate: int = 44100,
    duration: float = 1.0,
    click_rate: float = 10.0,
    click_amplitude: float = 0.5,
    click_duration: float = 0.001,  # in seconds (1 ms)
    polarity: str = "biphasic"      # or "positive"
) -> np.ndarray:
    """
    Generate a train of click sounds.

    Parameters:
        samplerate (int): Sampling rate in Hz.
        duration (float): Total duration of the signal in seconds.
        click_rate (float): Number of clicks per second (Hz).
        click_amplitude (float): Amplitude of each click (0–1).
        click_duration (float): Duration of each click in seconds.
        polarity (str): 'positive' (unipolar) or 'biphasic' (± pulse).

    Returns:
        np.ndarray: The generated click train waveform.
    """
    total_samples = int(samplerate * duration)
    click_samples = int(samplerate * click_duration)
    interval_samples = int(samplerate / click_rate)

    if click_samples >= interval_samples:
        raise ValueError(
            f"Click duration ({click_duration}s) is too long for the "
            f"given click rate ({click_rate} Hz). "
            "Increase the click rate or decrease click duration."
        )
        
    signal = np.zeros(total_samples)

    for i in range(0, total_samples, interval_samples):
        if i + click_samples >= total_samples:
            break
        if polarity == "positive":
            signal[i:i+click_samples] += click_amplitude
        elif polarity == "biphasic":
            half = click_samples // 2
            signal[i:i+half] += click_amplitude
            signal[i+half:i+click_samples] -= click_amplitude
        else:
            raise ValueError("polarity must be 'positive' or 'biphasic'")

    return signal

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

class AudioStimWorker(WorkerNode):

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