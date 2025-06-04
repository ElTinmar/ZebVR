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

    def layout_components(self) -> None:
        
        super().layout_components()
        self.main_layout.addWidget(self.stop_widget)

    def from_protocol_item(self, protocol_item: WhiteNoise) -> None:
        super().from_protocol_item(protocol_item)

    def to_protocol_item(self) -> WhiteNoise:
        return WhiteNoise(
            stop_condition = self.stop_widget.to_stop_condition()
        )

class PinkNoiseWidget(ProtocolItemWidget):

    def layout_components(self) -> None:
        
        super().layout_components()
        self.main_layout.addWidget(self.stop_widget)

    def from_protocol_item(self, protocol_item: PinkNoise) -> None:
        super().from_protocol_item(protocol_item)

    def to_protocol_item(self) -> PinkNoise:
        return PinkNoise(
            stop_condition = self.stop_widget.to_stop_condition()
        )

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
    