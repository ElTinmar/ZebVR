from ZebVR.protocol import (
    Stim, 
    ProtocolItem, 
    AudioProtocolItem,
    AudioProtocolItemWidget, 
    StopWidget, 
    Debouncer, 
    RampType
)
from typing import Dict
from PyQt5.QtWidgets import (
    QApplication, 
    QVBoxLayout,
    QGroupBox,
)
from qt_widgets import LabeledDoubleSpinBox, LabeledComboBox
from ..default import DEFAULT
from ...utils import set_from_dict

class FrequencyRamp(AudioProtocolItem):

    STIM_SELECT = Stim.FREQUENCY_RAMP

    def __init__(
            self, 
            ramp_start_Hz: float = DEFAULT['audio_ramp_start_Hz'],
            ramp_stop_Hz: float = DEFAULT['audio_ramp_stop_Hz'],
            ramp_duration_sec: float = DEFAULT['audio_ramp_duration_sec'],
            ramp_powerlaw_exponent: float = DEFAULT['audio_ramp_powerlaw_exponent'],
            ramp_type: RampType = DEFAULT['audio_ramp_type'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.ramp_start_Hz = ramp_start_Hz
        self.ramp_stop_Hz = ramp_stop_Hz 
        self.ramp_duration_sec = ramp_duration_sec
        self.ramp_powerlaw_exponent = ramp_powerlaw_exponent
        self.ramp_type = ramp_type

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'ramp_start_Hz': self.ramp_start_Hz,
            'ramp_stop_Hz': self.ramp_stop_Hz,
            'amplitude_dB': self.amplitude_dB,
            'ramp_powerlaw_exponent': self.ramp_powerlaw_exponent,
            'ramp_duration_sec': self.ramp_duration_sec,
            'ramp_type': self.ramp_type
        }
        return command
    
class FrequencyRampWidget(AudioProtocolItemWidget):
    
    RAMPS = (RampType.LINEAR, RampType.POWER_LAW, RampType.LOG) 

    def __init__(
            self,
            ramp_start_Hz: float = DEFAULT['audio_ramp_start_Hz'],
            ramp_stop_Hz: float = DEFAULT['audio_ramp_stop_Hz'],
            ramp_duration_sec: float = DEFAULT['audio_ramp_duration_sec'],
            ramp_powerlaw_exponent: float = DEFAULT['audio_ramp_powerlaw_exponent'],
            ramp_type: RampType = DEFAULT['audio_ramp_type'],
            *args,
            **kwargs
        ) -> None:

        self.ramp_start_Hz = ramp_start_Hz
        self.ramp_stop_Hz = ramp_stop_Hz
        self.ramp_powerlaw_exponent = ramp_powerlaw_exponent
        self.ramp_duration_sec = ramp_duration_sec
        self.ramp_type = ramp_type

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:
        
        super().declare_components()

        self.sb_ramp_start_Hz = LabeledDoubleSpinBox()
        self.sb_ramp_start_Hz.setText('Frequency start (Hz)')
        self.sb_ramp_start_Hz.setRange(0.1, 10000.0)
        self.sb_ramp_start_Hz.setValue(self.ramp_start_Hz)
        self.sb_ramp_start_Hz.valueChanged.connect(self.state_changed)

        self.sb_ramp_stop_Hz = LabeledDoubleSpinBox()
        self.sb_ramp_stop_Hz.setText('Frequency stop (Hz)')
        self.sb_ramp_stop_Hz.setRange(1, 100_000)
        self.sb_ramp_stop_Hz.setValue(self.ramp_stop_Hz)
        self.sb_ramp_stop_Hz.valueChanged.connect(self.state_changed)

        self.sb_ramp_duration_sec = LabeledDoubleSpinBox()
        self.sb_ramp_duration_sec.setText('Ramp duration (sec)')
        self.sb_ramp_duration_sec.setRange(0, 1_000.0)
        self.sb_ramp_duration_sec.setValue(self.ramp_duration_sec)
        self.sb_ramp_duration_sec.valueChanged.connect(self.state_changed)

        self.sb_ramp_powerlaw_exponent = LabeledDoubleSpinBox()
        self.sb_ramp_powerlaw_exponent.setText('Stevens exponent')
        self.sb_ramp_powerlaw_exponent.setRange(0.01, 20.0)
        self.sb_ramp_powerlaw_exponent.setValue(self.ramp_powerlaw_exponent)
        self.sb_ramp_powerlaw_exponent.valueChanged.connect(self.state_changed)

        self.cb_ramp_type = LabeledComboBox()
        self.cb_ramp_type.setText('Ramp type')
        for ramp_type in self.RAMPS:
            self.cb_ramp_type.addItem(str(ramp_type))
        self.cb_ramp_type.setCurrentIndex(self.ramp_type)
        self.cb_ramp_type.currentIndexChanged.connect(self.ramp_type_changed)

        self.ramp_type_changed()

    def ramp_type_changed(self) -> None:
        ramp_type = self.RAMPS[self.cb_ramp_type.currentIndex()]

        if ramp_type == RampType.LINEAR or ramp_type == RampType.LOG:
            self.sb_ramp_powerlaw_exponent.setVisible(False)

        if ramp_type == RampType.POWER_LAW:
            self.sb_ramp_powerlaw_exponent.setVisible(True)

        self.state_changed.emit()

    def layout_components(self) -> None:
        
        super().layout_components()

        frequency_layout = QVBoxLayout()
        frequency_layout.addWidget(self.sb_ramp_start_Hz)
        frequency_layout.addWidget(self.sb_ramp_stop_Hz)
        frequency_layout.addWidget(self.sb_ramp_duration_sec)
        frequency_layout.addWidget(self.sb_ramp_powerlaw_exponent)
        frequency_layout.addWidget(self.cb_ramp_type)
        frequency_layout.addStretch()

        self.frequency_group = QGroupBox('Frequency ramp parameters')
        self.frequency_group.setLayout(frequency_layout)

        self.main_layout.addWidget(self.frequency_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:

        state = super().get_state()
        state['ramp_start_Hz'] = self.sb_ramp_start_Hz.value()
        state['ramp_stop_Hz'] = self.sb_ramp_stop_Hz.value()
        state['ramp_duration_sec'] = self.sb_ramp_duration_sec.value()
        state['ramp_powerlaw_exponent'] = self.sb_ramp_powerlaw_exponent.value()
        state['ramp_type'] = self.RAMPS[self.cb_ramp_type.currentIndex()]
        return state

    def set_state(self, state: Dict) -> None:

        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'ramp_start_Hz',
            setter = self.sb_ramp_start_Hz.setValue,
            default = self.ramp_start_Hz,
            cast = float
        )   
        set_from_dict(
            dictionary = state,
            key = 'ramp_stop_Hz',
            setter = self.sb_ramp_stop_Hz.setValue,
            default = self.ramp_stop_Hz,
            cast = float
        )   
        set_from_dict(
            dictionary = state,
            key = 'ramp_duration_sec',
            setter = self.sb_ramp_duration_sec.setValue,
            default = self.ramp_duration_sec,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'ramp_powerlaw_exponent',
            setter = self.sb_ramp_powerlaw_exponent.setValue,
            default = self.ramp_powerlaw_exponent,
            cast = float
        )
        # TODO this is likely wrong
        set_from_dict(
            dictionary = state,
            key = 'ramp_type',
            setter = self.cb_ramp_type.setCurrentIndex,
            default = self.ramp_type
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:

        super().from_protocol_item(protocol_item)

        if isinstance(protocol_item, FrequencyRamp):
            self.sb_ramp_start_Hz.setValue(protocol_item.ramp_start_Hz)
            self.sb_ramp_stop_Hz.setValue(protocol_item.ramp_stop_Hz)
            self.cb_ramp_type.setCurrentIndex(protocol_item.ramp_type)
            self.sb_ramp_duration_sec.setValue(protocol_item.ramp_duration_sec)
            self.sb_ramp_powerlaw_exponent.setValue(protocol_item.ramp_powerlaw_exponent)

    def to_protocol_item(self) -> FrequencyRamp:

        protocol = FrequencyRamp(
            ramp_start_Hz = self.sb_ramp_start_Hz.value(),
            ramp_stop_Hz = self.sb_ramp_stop_Hz.value(),
            ramp_duration_sec = self.sb_ramp_duration_sec.value(),
            ramp_powerlaw_exponent = self.sb_ramp_powerlaw_exponent.value(),
            ramp_type = RampType(self.cb_ramp_type.currentIndex()),
            amplitude_dB = self.sb_amplitude_dB.value(),
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
    
