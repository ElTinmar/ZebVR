from ...protocol import Stim, ProtocolItem, VisualProtocolItemWidget, StopWidget, Debouncer, RampType
from typing import Tuple, Dict
from qt_widgets import LabeledDoubleSpinBox, LabeledComboBox
from PyQt5.QtWidgets import (
    QGroupBox, 
    QVBoxLayout,
    QApplication, 
)
from ...utils import set_from_dict
from ..default import DEFAULT

class BrightnessRamp(ProtocolItem):

    STIM_SELECT = Stim.BRIGHTNESS_RAMP

    def __init__(
            self, 
            brightness_start_percent: float = DEFAULT['brightness_start_percent'],
            brightness_stop_percent: float = DEFAULT['brightness_stop_percent'],
            brightness_ramp_rate_per_sec: float = DEFAULT['brightness_ramp_rate_per_sec'],
            brightness_ramp_type: RampType = DEFAULT['brightness_ramp_type'],
            foreground_color: Tuple[float, float, float, float] = DEFAULT['foreground_color'],
            background_color: Tuple[float, float, float, float] = DEFAULT['background_color'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.brightness_start_percent = brightness_start_percent
        self.brightness_stop_percent = brightness_stop_percent
        self.brightness_ramp_rate_per_sec = brightness_ramp_rate_per_sec
        self.brightness_ramp_type = brightness_ramp_type
        self.foreground_color = foreground_color 
        self.background_color = background_color 

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'brightness_start_percent': self.brightness_start_percent,
            'brightness_stop_percent': self.brightness_stop_percent,
            'brightness_ramp_rate_per_sec': self.brightness_ramp_rate_per_sec,
            'brightness_ramp_type': self.brightness_ramp_type,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color
        }
        return command
    
class BrightnessRampWidget(VisualProtocolItemWidget):

    def __init__(
            self, 
            brightness_start_percent: float = DEFAULT['brightness_start_percent'],
            brightness_stop_percent: float = DEFAULT['brightness_stop_percent'],
            brightness_ramp_rate_per_sec: float = DEFAULT['brightness_ramp_rate_per_sec'],
            brightness_ramp_type: RampType = DEFAULT['brightness_ramp_type'],
            foreground_color: Tuple[float, float, float, float] = DEFAULT['foreground_color'],
            background_color: Tuple[float, float, float, float] = DEFAULT['background_color'],
            *args,
            **kwargs
        ) -> None:
        
        self.brightness_start_percent = brightness_start_percent
        self.brightness_stop_percent = brightness_stop_percent
        self.brightness_ramp_rate_per_sec = brightness_ramp_rate_per_sec
        self.brightness_ramp_type = brightness_ramp_type
        self.foreground_color = foreground_color 
        self.background_color = background_color 

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:
        
        super().declare_components()

        self.sb_brightness_start_percent = LabeledDoubleSpinBox()
        self.sb_brightness_start_percent.setText('Brightness start (%)')
        self.sb_brightness_start_percent.setRange(0.0, 100.0)
        self.sb_brightness_start_percent.setValue(self.brightness_start_percent)
        self.sb_brightness_start_percent.valueChanged.connect(self.state_changed)

        self.sb_brightness_stop_percent = LabeledDoubleSpinBox()
        self.sb_brightness_stop_percent.setText('Brightness stop (%)')
        self.sb_brightness_stop_percent.setRange(0.0, 100.0)
        self.sb_brightness_stop_percent.setValue(self.brightness_stop_percent)
        self.sb_brightness_stop_percent.valueChanged.connect(self.state_changed)

        self.sb_ramp_rate_per_sec = LabeledDoubleSpinBox()
        self.sb_ramp_rate_per_sec.setText('Ramp rate')
        self.sb_ramp_rate_per_sec.setRange(-10_000.0, 10_000.0)
        self.sb_ramp_rate_per_sec.setValue(self.brightness_ramp_rate_per_sec)
        self.sb_ramp_rate_per_sec.valueChanged.connect(self.state_changed)

        self.cb_ramp_type = LabeledComboBox()
        self.cb_ramp_type.setText('Ramp type')
        for brightness_ramp_type in RampType:
            self.cb_ramp_type.addItem(str(brightness_ramp_type))
        self.cb_ramp_type.setCurrentIndex(self.brightness_ramp_type)
        self.cb_ramp_type.currentIndexChanged.connect(self.state_changed)

    def layout_components(self) -> None:
        
        super().layout_components()

        frequency_layout = QVBoxLayout()
        frequency_layout.addWidget(self.sb_brightness_start_percent)
        frequency_layout.addWidget(self.sb_brightness_stop_percent)
        frequency_layout.addWidget(self.sb_ramp_rate_per_sec)
        frequency_layout.addWidget(self.cb_ramp_type)
        frequency_layout.addStretch()

        self.frequency_group = QGroupBox('Brightness ramp parameters')
        self.frequency_group.setLayout(frequency_layout)

        self.main_layout.addWidget(self.frequency_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:

        state = super().get_state()
        state['brightness_start_percent'] = self.sb_brightness_start_percent.value()
        state['brightness_stop_percent'] = self.sb_brightness_stop_percent.value()
        state['brightness_ramp_rate_per_sec'] = self.sb_ramp_rate_per_sec.value()
        state['brightness_ramp_type'] = self.cb_ramp_type.currentIndex()
        return state
    
    def set_state(self, state: Dict) -> None:

        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'brightness_start_percent',
            setter = self.sb_brightness_start_percent.setValue,
            default = self.brightness_start_percent,
            cast = float
        )   
        set_from_dict(
            dictionary = state,
            key = 'brightness_stop_percent',
            setter = self.sb_brightness_stop_percent.setValue,
            default = self.brightness_stop_percent,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'brightness_ramp_rate_per_sec',
            setter = self.sb_ramp_rate_per_sec.setValue,
            default = self.sb_ramp_rate_per_sec,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'brightness_ramp_type',
            setter = self.cb_ramp_type.setCurrentIndex,
            default = self.brightness_ramp_type
        )

    def from_protocol_item(self, protocol_item: BrightnessRamp) -> None:

        super().from_protocol_item(protocol_item)

        self.sb_brightness_start_percent.setValue(protocol_item.brightness_start_percent)
        self.sb_brightness_stop_percent.setValue(protocol_item.brightness_stop_percent)
        self.cb_ramp_type.setCurrentIndex(protocol_item.brightness_ramp_type)
        self.sb_ramp_rate_per_sec.setValue(protocol_item.brightness_ramp_rate_per_sec)

    def to_protocol_item(self) -> BrightnessRamp:

        protocol = BrightnessRamp(
            brightness_start_percent = self.sb_brightness_start_percent.value(),
            brightness_stop_percent = self.sb_brightness_stop_percent.value(),
            brightness_ramp_rate_per_sec = self.sb_ramp_rate_per_sec.value(),
            brightness_ramp_type = RampType(self.cb_ramp_type.currentIndex()),
            stop_condition = self.stop_widget.to_stop_condition()
        )
        return protocol
    

if __name__ == '__main__':

    app = QApplication([])
    window = BrightnessRampWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
    
