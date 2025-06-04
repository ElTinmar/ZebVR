from ZebVR.protocol import Stim, ProtocolItem, ProtocolItemWidget, StopWidget, Debouncer
from typing import Tuple, Dict
from PyQt5.QtWidgets import (
    QApplication, 
)
from ..default import DEFAULT
from enum import IntEnum

class WhiteNoise(ProtocolItem):

    STIM_SELECT = Stim.WHITE_NOISE
    
    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
        }
        return command

class PinkNoise(ProtocolItem):

    STIM_SELECT = Stim.PINK_NOISE

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
        }
        return command
    
    
class WhiteNoiseWidget(ProtocolItemWidget):
    ...

class PinkNoiseWidget(ProtocolItemWidget):
    ...

if __name__ == '__main__':

    app = QApplication([])

    window0 = WhiteNoiseWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window0.show()

    window1 = PinkNoiseWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window1.show()

    app.exec()
    