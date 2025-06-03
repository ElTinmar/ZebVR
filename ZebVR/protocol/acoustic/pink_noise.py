from ZebVR.protocol import Stim, ProtocolItem, ProtocolItemWidget, StopWidget, Debouncer
from typing import Tuple, Dict
from PyQt5.QtWidgets import (
    QApplication, 
)
from ..default import DEFAULT

class PinkNoise(ProtocolItem):

    STIM_SELECT = Stim.PINK_NOISE

    def __init__(
            self, 
            duration_sec: float,
            t_rise_ms: float,
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.duration_sec = duration_sec
        self.t_rise_ms = t_rise_ms

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'duration_sec': self.duration_sec,
            't_rise_ms': self.t_rise_ms
        }
        return command
    
class PinkNoiseWidget(ProtocolItemWidget):
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
    