from ZebVR.protocol import Stim, ProtocolItem, ProtocolItemWidget, StopWidget, Debouncer
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
            amplitude_dB_SPL: float = DEFAULT['amplitude_dB_SPL'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.amplitude_dB_SPL = amplitude_dB_SPL

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'amplitude_dB_SPL': self.amplitude_dB_SPL
        }
        return command

class PinkNoise(ProtocolItem):

    STIM_SELECT = Stim.PINK_NOISE
    
    def __init__(
            self, 
            amplitude_dB_SPL: float = DEFAULT['amplitude_dB_SPL'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.amplitude_dB_SPL = amplitude_dB_SPL

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'amplitude_dB_SPL': self.amplitude_dB_SPL
        }
        return command


class WhiteNoiseWidget(ProtocolItemWidget):

    def __init__(
            self,
            amplitude_dB_SPL: float = DEFAULT['amplitude_dB_SPL'],
            *args,
            **kwargs
        ) -> None:

        self.amplitude_dB_SPL = amplitude_dB_SPL

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.sb_amplitude_dB_SPL = LabeledDoubleSpinBox()
        self.sb_amplitude_dB_SPL.setText('Amplitude SPL (dB)')
        self.sb_amplitude_dB_SPL.setRange(0.0, 200.0)
        self.sb_amplitude_dB_SPL.setValue(self.amplitude_dB_SPL)
        self.sb_amplitude_dB_SPL.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:
        
        super().layout_components()

        white_noise_layout = QVBoxLayout()
        white_noise_layout.addWidget(self.sb_amplitude_dB_SPL)
        white_noise_layout.addStretch()

        self.white_noise_group = QGroupBox('White noise parameters')
        self.white_noise_group.setLayout(white_noise_layout)

        self.main_layout.addWidget(self.white_noise_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:
        
        state = super().get_state()
        state['amplitude_dB_SPL'] = self.sb_amplitude_dB_SPL.value()
        return state
    

    def set_state(self, state: Dict) -> None:
        
        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'amplitude_dB_SPL',
            setter = self.sb_amplitude_dB_SPL.setValue,
            default = self.amplitude_dB_SPL,
            cast = float
        )

    def from_protocol_item(self, protocol_item: WhiteNoise) -> None:

        super().from_protocol_item(protocol_item)
        self.sb_amplitude_dB_SPL.setValue(protocol_item.amplitude_dB_SPL)

    def to_protocol_item(self) -> WhiteNoise:
        return WhiteNoise(
            amplitude_dB_SPL = self.sb_amplitude_dB_SPL.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )

class PinkNoiseWidget(ProtocolItemWidget):

    def __init__(
            self,
            amplitude_dB_SPL: float = DEFAULT['amplitude_dB_SPL'],
            *args,
            **kwargs
        ) -> None:

        self.amplitude_dB_SPL = amplitude_dB_SPL

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.sb_amplitude_dB_SPL = LabeledDoubleSpinBox()
        self.sb_amplitude_dB_SPL.setText('Amplitude SPL (dB)')
        self.sb_amplitude_dB_SPL.setRange(0.0, 200.0)
        self.sb_amplitude_dB_SPL.setValue(self.amplitude_dB_SPL)
        self.sb_amplitude_dB_SPL.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:

        super().layout_components()

        pink_noise_layout = QVBoxLayout()
        pink_noise_layout.addWidget(self.sb_amplitude_dB_SPL)
        pink_noise_layout.addStretch()

        self.pink_noise_group = QGroupBox('Pink noise parameters')
        self.pink_noise_group.setLayout(pink_noise_layout)

        self.main_layout.addWidget(self.pink_noise_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:
        
        state = super().get_state()
        state['amplitude_dB_SPL'] = self.sb_amplitude_dB_SPL.value()
        return state

    def set_state(self, state: Dict) -> None:
        
        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'amplitude_dB_SPL',
            setter = self.sb_amplitude_dB_SPL.setValue,
            default = self.amplitude_dB_SPL,
            cast = float
        )

    def from_protocol_item(self, protocol_item: PinkNoise) -> None:

        super().from_protocol_item(protocol_item)
        self.sb_amplitude_dB_SPL.setValue(protocol_item.amplitude_dB_SPL)

    def to_protocol_item(self) -> PinkNoise:

        return PinkNoise(
            amplitude_dB_SPL = self.sb_amplitude_dB_SPL.value(),
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
    