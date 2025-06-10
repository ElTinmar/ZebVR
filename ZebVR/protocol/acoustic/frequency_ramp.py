from ZebVR.protocol import Stim, ProtocolItem, ProtocolItemWidget, StopWidget, Debouncer, RampType
from typing import Dict
from PyQt5.QtWidgets import (
    QApplication, 
    QVBoxLayout,
    QGroupBox,
)
from qt_widgets import LabeledDoubleSpinBox, LabeledComboBox
from ..default import DEFAULT
from ...utils import set_from_dict
    
class FrequencyRamp(ProtocolItem):

    STIM_SELECT = Stim.FREQUENCY_RAMP

    def __init__(
            self, 
            frequency_start_Hz: float = DEFAULT['frequency_start_Hz'],
            amplitude_dB_SPL: float = DEFAULT['amplitude_dB_SPL'],
            frequency_ramp_rate_per_sec: float = DEFAULT['frequency_ramp_rate_per_sec'],
            frequency_ramp_type: RampType = DEFAULT['frequency_ramp_type'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.frequency_start_Hz = frequency_start_Hz 
        self.amplitude_dB_SPL = amplitude_dB_SPL
        self.frequency_ramp_rate_per_sec = frequency_ramp_rate_per_sec
        self.frequency_ramp_type = frequency_ramp_type

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'frequency_start_Hz': self.frequency_start_Hz,
            'amplitude_dB_SPL': self.amplitude_dB_SPL,
            'frequency_ramp_rate_per_sec': self.frequency_ramp_rate_per_sec,
            'frequency_ramp_type': self.frequency_ramp_type
        }
        return command
    
class FrequencyRampWidget(ProtocolItemWidget):
    
    def __init__(
            self,
            frequency_start_Hz: float = DEFAULT['frequency_start_Hz'],
            amplitude_dB_SPL: float = DEFAULT['amplitude_dB_SPL'],
            frequency_ramp_rate_per_sec: float = DEFAULT['frequency_ramp_rate_per_sec'],
            frequency_ramp_type: RampType = DEFAULT['frequency_ramp_type'],
            *args,
            **kwargs
        ) -> None:

        self.frequency_start_Hz = frequency_start_Hz
        self.amplitude_dB_SPL = amplitude_dB_SPL
        self.frequency_ramp_rate_per_sec = frequency_ramp_rate_per_sec
        self.frequency_ramp_type = frequency_ramp_type

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:
        
        super().declare_components()

        self.sb_frequency_start_Hz = LabeledDoubleSpinBox()
        self.sb_frequency_start_Hz.setText('Frequency start (Hz)')
        self.sb_frequency_start_Hz.setRange(0.1, 10000.0)
        self.sb_frequency_start_Hz.setValue(self.frequency_start_Hz)
        self.sb_frequency_start_Hz.valueChanged.connect(self.state_changed)

        self.sb_amplitude_dB_SPL = LabeledDoubleSpinBox()
        self.sb_amplitude_dB_SPL.setText('Amplitude SPL (dB)')
        self.sb_amplitude_dB_SPL.setRange(0.0, 200.0)
        self.sb_amplitude_dB_SPL.setValue(self.amplitude_dB_SPL)
        self.sb_amplitude_dB_SPL.valueChanged.connect(self.state_changed)

        self.sb_ramp_rate_per_sec = LabeledDoubleSpinBox()
        self.sb_ramp_rate_per_sec.setText('Ramp rate')
        self.sb_ramp_rate_per_sec.setRange(-10_000.0, 10_000.0)
        self.sb_ramp_rate_per_sec.setValue(self.frequency_ramp_rate_per_sec)
        self.sb_ramp_rate_per_sec.valueChanged.connect(self.state_changed)

        self.cb_ramp_type = LabeledComboBox()
        self.cb_ramp_type.setText('Ramp type')
        for frequency_ramp_type in RampType:
            self.cb_ramp_type.addItem(str(frequency_ramp_type))
        self.cb_ramp_type.setCurrentIndex(self.frequency_ramp_type)
        self.cb_ramp_type.currentIndexChanged.connect(self.state_changed)

    def layout_components(self) -> None:
        
        super().layout_components()

        frequency_layout = QVBoxLayout()
        frequency_layout.addWidget(self.sb_frequency_start_Hz)
        frequency_layout.addWidget(self.sb_amplitude_dB_SPL)
        frequency_layout.addWidget(self.sb_ramp_rate_per_sec)
        frequency_layout.addWidget(self.cb_ramp_type)
        frequency_layout.addStretch()

        self.frequency_group = QGroupBox('Frequency ramp parameters')
        self.frequency_group.setLayout(frequency_layout)

        self.main_layout.addWidget(self.frequency_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:

        state = super().get_state()
        state['frequency_start_Hz'] = self.sb_frequency_start_Hz.value()
        state['amplitude_dB_SPL'] = self.sb_amplitude_dB_SPL.value()
        state['frequency_ramp_rate_per_sec'] = self.sb_ramp_rate_per_sec.value()
        state['frequency_ramp_type'] = self.cb_ramp_type.currentIndex()
        return state

    def set_state(self, state: Dict) -> None:

        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'frequency_start_Hz',
            setter = self.sb_frequency_start_Hz.setValue,
            default = self.frequency_start_Hz,
            cast = float
        )   
        set_from_dict(
            dictionary = state,
            key = 'amplitude_dB_SPL',
            setter = self.sb_amplitude_dB_SPL.setValue,
            default = self.amplitude_dB_SPL,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'frequency_ramp_rate_per_sec',
            setter = self.sb_ramp_rate_per_sec.setValue,
            default = self.sb_ramp_rate_per_sec,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'frequency_ramp_type',
            setter = self.cb_ramp_type.setCurrentIndex,
            default = self.frequency_ramp_type
        )

    def from_protocol_item(self, protocol_item: FrequencyRamp) -> None:

        super().from_protocol_item(protocol_item)

        self.sb_frequency_start_Hz.setValue(protocol_item.frequency_start_Hz)
        self.cb_ramp_type.setCurrentIndex(protocol_item.frequency_ramp_type)
        self.sb_ramp_rate_per_sec.setValue(protocol_item.frequency_ramp_rate_per_sec)
        self.sb_amplitude_dB_SPL.setValue(protocol_item.amplitude_dB_SPL)

    def to_protocol_item(self) -> FrequencyRamp:

        protocol = FrequencyRamp(
            frequency_start_Hz = self.sb_frequency_start_Hz.value(),
            frequency_ramp_rate_per_sec = self.sb_ramp_rate_per_sec.value(),
            frequency_ramp_type = RampType(self.cb_ramp_type.currentIndex()),
            amplitude_dB_SPL = self.sb_amplitude_dB_SPL.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )
        return protocol
    

if __name__ == '__main__':

    app = QApplication([])
    window = FrequencyRampWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
    
