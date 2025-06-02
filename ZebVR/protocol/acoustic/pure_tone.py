from ...protocol import Stim, ProtocolItem, ProtocolItemWidget, StopWidget, Debouncer
from typing import Tuple, Dict
from PyQt5.QtWidgets import (
    QApplication, 
)
class PureTone(ProtocolItem):

    STIM_SELECT = Stim.Acoustic.PURE_TONE

    def __init__(
            self, 
            frequency_Hz: float,
            duration_sec: float,
            t_rise_ms: float,
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.frequency_Hz = frequency_Hz 
        self.duration_sec = duration_sec
        self.t_rise_ms = t_rise_ms

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'frequency_Hz': self.frequency_Hz,
            'duration_sec': self.duration_sec,
            't_rise_ms': self.t_rise_ms
        }
        return command
    
class PureToneWidget(ProtocolItemWidget):
    ...