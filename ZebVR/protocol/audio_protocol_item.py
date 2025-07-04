from .protocol_item import AudioProtocolItem, ProtocolItem, ProtocolItemWidget
from .default import DEFAULT
from typing import Tuple, Dict
from qt_widgets import LabeledDoubleSpinBox
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QLabel,
    QHBoxLayout,
)
from ..utils import set_from_dict

class AudioProtocolItemWidget(ProtocolItemWidget):
    
    state_changed = pyqtSignal()

    def __init__(
            self,
            amplitude_dB: float = DEFAULT['amplitude_dB'],
            *args,
            **kwargs
        ) -> None:

        self.amplitude_dB = amplitude_dB

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.sb_amplitude_dB = LabeledDoubleSpinBox()
        self.sb_amplitude_dB.setText('amplitude (dB)')
        self.sb_amplitude_dB.setRange(0, 200)
        self.sb_amplitude_dB.setSingleStep(1)
        self.sb_amplitude_dB.setValue(self.amplitude_dB)
        self.sb_amplitude_dB.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:

        super().layout_components()

        self.main_layout.addWidget(self.sb_amplitude_dB)

    def get_state(self) -> Dict:

        state = super().get_state()
        state['amplitude_dB'] = self.sb_amplitude_dB.value()
        return state

    def set_state(self, state: Dict) -> None:

        super().set_state(state)
        
        set_from_dict(
            dictionary = state,
            key = 'amplitude_dB',
            setter = self.sb_amplitude_dB.setValue,
            default = self.amplitude_dB,
            cast = float
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:
        
        if isinstance(protocol_item, AudioProtocolItem):
            self.sb_amplitude_dB.setValue(protocol_item.amplitude_dB)

    def to_protocol_item(self) -> AudioProtocolItem:
        ...

