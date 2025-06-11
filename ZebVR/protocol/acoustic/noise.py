from ZebVR.protocol import Stim, ProtocolItem, AudioProtocolItemWidget, StopWidget, Debouncer
from typing import Tuple, Dict
from qt_widgets import LabeledDoubleSpinBox
from PyQt5.QtWidgets import (
    QGroupBox, 
    QVBoxLayout,
    QApplication, 
)
from ..default import DEFAULT
from ...utils import set_from_dict

class WhiteNoise(ProtocolItem):

    STIM_SELECT = Stim.WHITE_NOISE

    def __init__(
            self, 
            amplitude_dB: float = DEFAULT['amplitude_dB'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.amplitude_dB = amplitude_dB

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'amplitude_dB': self.amplitude_dB
        }
        return command

class PinkNoise(ProtocolItem):

    STIM_SELECT = Stim.PINK_NOISE
    
    def __init__(
            self, 
            amplitude_dB: float = DEFAULT['amplitude_dB'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.amplitude_dB = amplitude_dB

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'amplitude_dB': self.amplitude_dB
        }
        return command


class WhiteNoiseWidget(AudioProtocolItemWidget):

    def layout_components(self) -> None:
        
        super().layout_components()
        self.main_layout.addWidget(self.stop_widget)

    def to_protocol_item(self) -> WhiteNoise:

        return WhiteNoise(
            amplitude_dB_SPL = self.sb_amplitude_dB.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )

class PinkNoiseWidget(AudioProtocolItemWidget):

    def layout_components(self) -> None:
        
        super().layout_components()
        self.main_layout.addWidget(self.stop_widget)
        
    def to_protocol_item(self) -> PinkNoise:

        return PinkNoise(
            amplitude_dB = self.sb_amplitude_dB.value(),
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
    