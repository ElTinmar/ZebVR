from ZebVR.protocol import Stim, ProtocolItem, ProtocolItemWidget, StopWidget, Debouncer
from typing import Tuple, Dict
from PyQt5.QtWidgets import (
    QApplication, 
)
from ..default import DEFAULT

class PureTone(ProtocolItem):

    STIM_SELECT = Stim.PURE_TONE

    def __init__(
            self, 
            frequency_Hz: float,
            t_rise_ms: float,
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.frequency_Hz = frequency_Hz 
        self.t_rise_ms = t_rise_ms

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'frequency_Hz': self.frequency_Hz,
            't_rise_ms': self.t_rise_ms
        }
        return command
    
class PureToneWidget(ProtocolItemWidget):
    ...

if __name__ == '__main__':

    app = QApplication([])
    window = PureToneWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
    