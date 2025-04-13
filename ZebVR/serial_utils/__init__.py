from typing import List
from serial.tools.list_ports import comports

def get_serial() -> List[str]:
    ports = comports()
    return [p.device for p in ports if p.hwid != 'n/a']