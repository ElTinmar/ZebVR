from ctypes import c_char
from multiprocessing import RawArray

class SharedString:
    def __init__(
            self, 
            max_length: int = 1024, 
            initializer: str = ''
        ):
        self.buf = RawArray(c_char, max_length)
        self.set(initializer)

    def set(self, s: str):
        encoded = s.encode('utf-8')
        if len(encoded) >= len(self.buf):
            raise ValueError("String too long for shared buffer")
        self.buf[:len(encoded)] = encoded
        self.buf[len(encoded)] = 0  # null-terminate

    def get(self) -> str:
        raw_bytes = bytearray()
        for b in self.buf:
            if b == b'\x00': # null terminator
                break
            raw_bytes.append(b[0])
        return raw_bytes.decode('utf-8')
    
    def __str__(self) -> str:
        return self.get()

    def __repr__(self) -> str:
        return f"SharedString('{self.get()}')"

    @property
    def value(self) -> str:
        return self.get()

    @value.setter
    def value(self, s: str):
        self.set(s)
        