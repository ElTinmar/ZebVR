from ZebVR.protocol import (
    Stim, 
    ProtocolItem, 
    AudioProtocolItem,
    AudioProtocolItemWidget, 
    StopWidget, 
    Debouncer
)
from typing import Dict, Any
from qt_widgets import LabeledDoubleSpinBox
from qtpy.QtWidgets import (
    QGroupBox, 
    QVBoxLayout,
    QApplication, 
)
from ...utils import set_from_dict
from ..default import DEFAULT

class PureTone(AudioProtocolItem):

    STIM_SELECT = Stim.PURE_TONE

    def __init__(
            self, 
            frequency_Hz: float = DEFAULT['frequency_Hz'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.frequency_Hz = frequency_Hz

    def start(self) -> Dict:

        command = super().start()
        command.update({
            'stim_select': self.STIM_SELECT,
            'frequency_Hz': self.frequency_Hz,
        })
        return command

class PureToneWidget(AudioProtocolItemWidget):
    
    def __init__(
            self,
            frequency_Hz: float = DEFAULT['frequency_Hz'],
            *args,
            **kwargs
        ) -> None:

        self.frequency_Hz = frequency_Hz

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.sb_frequency_Hz = LabeledDoubleSpinBox()
        self.sb_frequency_Hz.setText('Frequency (Hz)')
        self.sb_frequency_Hz.setRange(0.1, 10_000.0)
        self.sb_frequency_Hz.setValue(self.frequency_Hz)
        self.sb_frequency_Hz.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:
        
        super().layout_components()

        tone_layout = QVBoxLayout()
        tone_layout.addWidget(self.sb_frequency_Hz)
        tone_layout.addStretch()

        self.tone_group = QGroupBox('Pure tone parameters')
        self.tone_group.setLayout(tone_layout)

        self.main_layout.addWidget(self.tone_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:
        
        state = super().get_state()
        state['frequency_Hz'] = self.sb_frequency_Hz.value()
        return state

    def set_state(self, state: Dict) -> None:
        
        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'frequency_Hz',
            setter = self.sb_frequency_Hz.setValue,
            default = self.frequency_Hz,
            cast = float
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:

        super().from_protocol_item(protocol_item)
    
        if isinstance(protocol_item, PureTone):
            self.sb_frequency_Hz.setValue(protocol_item.frequency_Hz)

    def _get_protocol_kwargs(self) -> Dict[str, Any]:
        kwargs = super()._get_protocol_kwargs()
        kwargs.update({
            'frequency_Hz': self.sb_frequency_Hz.value()
        })
        return kwargs
    
    def to_protocol_item(self) -> PureTone:
        return PureTone(**self._get_protocol_kwargs())

if __name__ == '__main__':

    app = QApplication([])
    window = PureToneWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
    