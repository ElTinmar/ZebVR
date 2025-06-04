from ZebVR.protocol import Stim, ProtocolItem, ProtocolItemWidget, StopWidget, Debouncer
from typing import Dict
from qt_widgets import LabeledDoubleSpinBox
from PyQt5.QtWidgets import (
    QGroupBox, 
    QVBoxLayout,
    QApplication, 
)
from ...utils import set_from_dict
from ..default import DEFAULT

class PureTone(ProtocolItem):

    STIM_SELECT = Stim.PURE_TONE

    def __init__(
            self, 
            frequency_Hz: float = DEFAULT['frequency_Hz'],
            amplitude_dB_SPL: float = DEFAULT['amplitude_dB_SPL'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.frequency_Hz = frequency_Hz
        self.amplitude_dB_SPL = amplitude_dB_SPL

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'frequency_Hz': self.frequency_Hz,
            'amplitude_dB_SPL': self.amplitude_dB_SPL
        }
        return command

class PureToneWidget(ProtocolItemWidget):
    
    def __init__(
            self,
            frequency_Hz: float = DEFAULT['frequency_Hz'],
            amplitude_dB_SPL: float = DEFAULT['amplitude_dB_SPL'],
            *args,
            **kwargs
        ) -> None:

        self.frequency_Hz = frequency_Hz
        self.amplitude_dB_SPL = amplitude_dB_SPL

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.sb_frequency_Hz = LabeledDoubleSpinBox()
        self.sb_frequency_Hz.setText('Frequency (Hz)')
        self.sb_frequency_Hz.setRange(0.1, 10_000.0)
        self.sb_frequency_Hz.setValue(self.frequency_Hz)
        self.sb_frequency_Hz.valueChanged.connect(self.state_changed)

        self.sb_amplitude_dB_SPL = LabeledDoubleSpinBox()
        self.sb_amplitude_dB_SPL.setText('Amplitude SPL (dB)')
        self.sb_amplitude_dB_SPL.setRange(0.0, 200.0)
        self.sb_amplitude_dB_SPL.setValue(self.amplitude_dB_SPL)
        self.sb_amplitude_dB_SPL.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:
        
        super().layout_components()

        tone_layout = QVBoxLayout()
        tone_layout.addWidget(self.sb_frequency_Hz)
        tone_layout.addWidget(self.sb_amplitude_dB_SPL)
        tone_layout.addStretch()

        self.tone_group = QGroupBox('Pure tone parameters')
        self.tone_group.setLayout(tone_layout)

        self.main_layout.addWidget(self.tone_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:
        
        state = super().get_state()
        state['frequency_Hz'] = self.sb_frequency_Hz.value()
        state['amplitude_dB_SPL'] = self.sb_amplitude_dB_SPL.value()
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
        set_from_dict(
            dictionary = state,
            key = 'amplitude_dB_SPL',
            setter = self.sb_amplitude_dB_SPL.setValue,
            default = self.amplitude_dB_SPL,
            cast = float
        )

    def from_protocol_item(self, protocol_item: PureTone) -> None:

        super().from_protocol_item(protocol_item)
        self.sb_frequency_Hz.setValue(protocol_item.frequency_Hz)
        self.sb_amplitude_dB_SPL.setValue(protocol_item.amplitude_dB_SPL)

    def to_protocol_item(self) -> PureTone:
        
        return PureTone(
            frequency_Hz = self.sb_frequency_Hz.value(),
            amplitude_dB_SPL = self.sb_amplitude_dB_SPL.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )

if __name__ == '__main__':

    app = QApplication([])
    window = PureToneWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
    