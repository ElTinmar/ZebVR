from ZebVR.protocol import Stim, ProtocolItem, ProtocolItemWidget, StopWidget, Debouncer
from typing import Tuple, Dict
from PyQt5.QtWidgets import (
    QApplication, 
)
from ..default import DEFAULT

class FrequencyRamp(ProtocolItem):

    STIM_SELECT = Stim.FREQUENCY_RAMP

    def __init__(
            self, 
            frequency_Hz_start: float,
            frequency_Hz_stop: float,
            duration_sec: float,
            t_rise_ms: float,
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.frequency_Hz_start = frequency_Hz_start 
        self.frequency_Hz_stop = frequency_Hz_stop
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
    
class FrequencyRampWidget(ProtocolItemWidget):
    ...

if __name__ == '__main__':

    app = QApplication([])
    window = FrequencyRampWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
    
