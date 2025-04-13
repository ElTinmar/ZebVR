from typing import List, NamedTuple
from serial.tools.list_ports import comports

ARDUINO_VID = 0x2341

class SerialDevice(NamedTuple):
    device: str
    description: str

def list_serial_devices() -> List[SerialDevice]:
    ports = comports()
    return [SerialDevice(p.device, p.description) for p in ports if p.hwid != 'n/a']

def list_serial_arduino() -> List[SerialDevice]:
    ports = comports()
    return [SerialDevice(p.device, p.description) for p in ports if p.vid == ARDUINO_VID]