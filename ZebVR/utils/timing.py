import time
import platform

def get_time_ns() -> int:
    """
    Return a high-resolution, system-wide, monotonic timestamp in nanoseconds.
    On Windows with Python < 3.10, use monotonic_ns() for system-wide behavior.
    Elsewhere (or Python ≥ 3.10), use perf_counter_ns() for best resolution.
    """

    is_windows = platform.system() == "Windows"

    if is_windows:
        return time.monotonic_ns()
    
    return time.perf_counter_ns()
        
            
