from pathlib import Path
import os
from typing import Union
import time
import locale
import contextlib

@contextlib.contextmanager
def english_locale():
    saved = locale.setlocale(locale.LC_TIME)
    try:
        locale.setlocale(locale.LC_TIME, 'C')
        yield
    finally:
        locale.setlocale(locale.LC_TIME, saved)

def timestamp() -> str:
    with english_locale():
        return time.strftime('%a_%d_%b_%Y_%Hh%Mmin%Ssec')

def append_timestamp_to_filename(filename: Union[Path, str]):

    filename = Path(filename)
    prefix = filename.stem
    extension = filename.suffix
    parent = filename.parent

    
    new_name = f"{prefix}_{timestamp()}{extension}"
    new_path = parent / new_name

    while new_path.exists():
        time.sleep(1)
        new_name = f"{prefix}_{timestamp()}{extension}"
        new_path = parent / new_name

    return new_path