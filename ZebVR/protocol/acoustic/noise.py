from ZebVR.protocol import Stim, ProtocolItem, ProtocolItemWidget, StopWidget, Debouncer
from typing import Tuple, Dict
from PyQt5.QtWidgets import (
    QApplication, 
)
from ..default import DEFAULT
from enum import IntEnum

class NoiseType(IntEnum):
    WHITE = 0
    PINK = 1

    def __str__(self):
        return self.name

class Noise(ProtocolItem):

    STIM_SELECT = Stim.NOISE

    def __init__(
            self, 
            frequency_low_Hz: float,
            frequency_high_Hz: float,
            t_rise_ms: float,
            noise_type: NoiseType,
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.frequency_low_Hz = frequency_low_Hz
        self.frequency_high_Hz = frequency_high_Hz
        self.noise_type = noise_type
        self.t_rise_ms = t_rise_ms

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'frequency_low_Hz': self.frequency_low_Hz,
            'frequency_high_Hz': self.frequency_high_Hz,
            'noise_type': self.noise_type,
            't_rise_ms': self.t_rise_ms
        }
        return command
    
class NoiseWidget(ProtocolItemWidget):
    ...

if __name__ == '__main__':

    app = QApplication([])
    window = PinkNoiseWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
    