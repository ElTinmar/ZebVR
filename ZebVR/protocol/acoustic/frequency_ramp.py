from ZebVR.protocol import Stim, ProtocolItem, ProtocolItemWidget, StopWidget, Debouncer
from typing import Dict
from PyQt5.QtWidgets import (
    QApplication, 
    QVBoxLayout,
    QGroupBox,
)
from qt_widgets import LabeledDoubleSpinBox, LabeledComboBox
from ..default import DEFAULT
from ...utils import set_from_dict
from enum import IntEnum

class SweepType(IntEnum):
    LOG = 0
    LINEAR = 1

    def __str__(self) -> str:
        return self.name
    
class FrequencyRamp(ProtocolItem):

    STIM_SELECT = Stim.FREQUENCY_RAMP

    def __init__(
            self, 
            frequency_Hz_start: float = DEFAULT['frequency_Hz_start'],
            frequency_Hz_stop: float = DEFAULT['frequency_Hz_stop'],
            amplitude_dB_SPL: float = DEFAULT['amplitude_dB_SPL'],
            sweep_type: SweepType = DEFAULT['sweep_type'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.frequency_Hz_start = frequency_Hz_start 
        self.frequency_Hz_stop = frequency_Hz_stop
        self.amplitude_dB_SPL = amplitude_dB_SPL    
        self.sweep_type = sweep_type

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'frequency_Hz_start': self.frequency_Hz_start,
            'frequency_Hz_stop': self.frequency_Hz_stop,
            'amplitude_dB_SPL': self.amplitude_dB_SPL,
            'sweep_type': self.sweep_type
        }
        return command
    
class FrequencyRampWidget(ProtocolItemWidget):
    
    def __init__(
            self,
            frequency_Hz_start: float = DEFAULT['frequency_Hz_start'],
            frequency_Hz_stop: float = DEFAULT['frequency_Hz_stop'],
            amplitude_dB_SPL: float = DEFAULT['amplitude_dB_SPL'],
            sweep_type: SweepType = DEFAULT['sweep_type'],
            *args,
            **kwargs
        ) -> None:

        self.frequency_Hz_start = frequency_Hz_start
        self.frequency_Hz_stop = frequency_Hz_stop
        self.amplitude_dB_SPL = amplitude_dB_SPL
        self.sweep_type = sweep_type

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:
        
        super().declare_components()

        self.sb_frequency_Hz_start = LabeledDoubleSpinBox()
        self.sb_frequency_Hz_start.setText('Frequency start (Hz)')
        self.sb_frequency_Hz_start.setRange(0.1, 10000.0)
        self.sb_frequency_Hz_start.setValue(self.frequency_Hz_start)
        self.sb_frequency_Hz_start.valueChanged.connect(self.state_changed)

        self.sb_frequency_Hz_stop = LabeledDoubleSpinBox()
        self.sb_frequency_Hz_stop.setText('Frequency stop (Hz)')
        self.sb_frequency_Hz_stop.setRange(0.1, 10000.0)
        self.sb_frequency_Hz_stop.setValue(self.frequency_Hz_stop)
        self.sb_frequency_Hz_stop.valueChanged.connect(self.state_changed)

        self.sb_amplitude_dB_SPL = LabeledDoubleSpinBox()
        self.sb_amplitude_dB_SPL.setText('Amplitude SPL (dB)')
        self.sb_amplitude_dB_SPL.setRange(0.0, 200.0)
        self.sb_amplitude_dB_SPL.setValue(self.amplitude_dB_SPL)
        self.sb_amplitude_dB_SPL.valueChanged.connect(self.state_changed)

        self.cb_sweep_type = LabeledComboBox()
        self.cb_sweep_type.setText('Sweep type')
        for sweep_type in SweepType:
            self.cb_sweep_type.addItem(str(sweep_type))
        self.cb_sweep_type.setCurrentIndex(self.sweep_type)
        self.cb_sweep_type.currentIndexChanged.connect(self.state_changed)

    def layout_components(self) -> None:
        
        super().layout_components()

        frequency_layout = QVBoxLayout()
        frequency_layout.addWidget(self.sb_frequency_Hz_start)
        frequency_layout.addWidget(self.sb_frequency_Hz_stop)
        frequency_layout.addWidget(self.sb_amplitude_dB_SPL)
        frequency_layout.addWidget(self.cb_sweep_type)
        frequency_layout.addStretch()

        self.frequency_group = QGroupBox('Frequency sweep parameters')
        self.frequency_group.setLayout(frequency_layout)

        self.main_layout.addWidget(self.frequency_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:

        state = super().get_state()
        state['frequency_Hz_start'] = self.sb_frequency_Hz_start.value()
        state['frequency_Hz_stop'] = self.sb_frequency_Hz_stop.value()
        state['amplitude_dB_SPL'] = self.sb_amplitude_dB_SPL.value()
        state['sweep_type'] = self.cb_sweep_type.currentIndex()
        return state

    def set_state(self, state: Dict) -> None:

        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'frequency_Hz_start',
            setter = self.sb_frequency_Hz_start.setValue,
            default = self.frequency_Hz_start,
            cast = float
        )   
        set_from_dict(
            dictionary = state,
            key = 'frequency_Hz_stop',
            setter = self.sb_frequency_Hz_stop.setValue,
            default = self.frequency_Hz_stop,
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
            key = 'sweep_type',
            setter = self.cb_sweep_type.setCurrentIndex,
            default = self.sweep_type
        )

    def from_protocol_item(self, protocol_item: FrequencyRamp) -> None:

        super().from_protocol_item(protocol_item)

        self.sb_frequency_Hz_start.setValue(protocol_item.frequency_Hz_start)
        self.sb_frequency_Hz_stop.setValue(protocol_item.frequency_Hz_stop)
        self.cb_sweep_type.setCurrentIndex(protocol_item.sweep_type)
        self.sb_amplitude_dB_SPL.setValue(protocol_item.amplitude_dB_SPL)

    def to_protocol_item(self) -> FrequencyRamp:

        protocol = FrequencyRamp(
            frequency_Hz_start = self.sb_frequency_Hz_start.value(),
            frequency_Hz_stop = self.sb_frequency_Hz_stop.value(),
            sweep_type = SweepType(self.cb_sweep_type.currentIndex()),
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
    
