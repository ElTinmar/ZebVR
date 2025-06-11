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

class Ramp(ProtocolItem):

    STIM_SELECT = Stim.RAMP

    def __init__(
            self, 
            brightness_ramp_log_curvature: float = DEFAULT['brightness_ramp_log_curvature'],
            brightness_ramp_powerlaw_exponent: float = DEFAULT['brightness_ramp_powerlaw_exponent'],
            brightness_ramp_duration_sec: float = DEFAULT['brightness_ramp_duration_sec'],
            brightness_ramp_type: RampType = DEFAULT['brightness_ramp_type'],
            foreground_color: Tuple[float, float, float, float] = DEFAULT['foreground_color'],
            background_color: Tuple[float, float, float, float] = DEFAULT['background_color'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.brightness_ramp_log_curvature = brightness_ramp_log_curvature
        self.brightness_ramp_powerlaw_exponent = brightness_ramp_powerlaw_exponent
        self.brightness_ramp_duration_sec = brightness_ramp_duration_sec
        self.brightness_ramp_type = brightness_ramp_type
        self.foreground_color = foreground_color 
        self.background_color = background_color 

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'brightness_ramp_duration_sec': self.brightness_ramp_duration_sec,
            'brightness_ramp_log_curvature': self.brightness_ramp_log_curvature,
            'brightness_ramp_powerlaw_exponent': self.brightness_ramp_powerlaw_exponent,
            'brightness_ramp_type': self.brightness_ramp_type,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color
        }
        return command
    
class RampWidget(VisualProtocolItemWidget):

    def __init__(
            self, 
            brightness_ramp_duration_sec: float = DEFAULT['brightness_ramp_duration_sec'],
            brightness_ramp_log_curvature: float = DEFAULT['brightness_ramp_log_curvature'],
            brightness_ramp_powerlaw_exponent: float = DEFAULT['brightness_ramp_powerlaw_exponent'],
            brightness_ramp_type: RampType = DEFAULT['brightness_ramp_type'],
            foreground_color: Tuple[float, float, float, float] = DEFAULT['foreground_color'],
            background_color: Tuple[float, float, float, float] = DEFAULT['background_color'],
            *args,
            **kwargs
        ) -> None:
        
        self.brightness_ramp_duration_sec = brightness_ramp_duration_sec
        self.brightness_ramp_log_curvature = brightness_ramp_log_curvature
        self.brightness_ramp_powerlaw_exponent = brightness_ramp_powerlaw_exponent
        self.brightness_ramp_type = brightness_ramp_type
        self.foreground_color = foreground_color 
        self.background_color = background_color 

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:
        
        super().declare_components()

        self.sb_ramp_duration_sec = LabeledDoubleSpinBox()
        self.sb_ramp_duration_sec.setText('Ramp duration (sec)')
        self.sb_ramp_duration_sec.setRange(0.1, 1_000.0)
        self.sb_ramp_duration_sec.setValue(self.brightness_ramp_duration_sec)
        self.sb_ramp_duration_sec.valueChanged.connect(self.state_changed)

        self.sb_ramp_log_curvature = LabeledDoubleSpinBox()
        self.sb_ramp_log_curvature.setText('Log curvature')
        self.sb_ramp_log_curvature.setRange(0.01, 100.0)
        self.sb_ramp_log_curvature.setValue(self.brightness_ramp_log_curvature)
        self.sb_ramp_log_curvature.valueChanged.connect(self.state_changed)

        self.sb_ramp_powerlaw_exponent = LabeledDoubleSpinBox()
        self.sb_ramp_powerlaw_exponent.setText('Power-law exponent')
        self.sb_ramp_powerlaw_exponent.setRange(0.01, 20.0)
        self.sb_ramp_powerlaw_exponent.setValue(self.brightness_ramp_powerlaw_exponent)
        self.sb_ramp_powerlaw_exponent.valueChanged.connect(self.state_changed)

        self.cb_ramp_type = LabeledComboBox()
        self.cb_ramp_type.setText('Ramp type')
        for ramp_type in RampType:
            self.cb_ramp_type.addItem(str(ramp_type))
        self.cb_ramp_type.currentIndexChanged.connect(self.ramp_type_changed)
        self.cb_ramp_type.setCurrentIndex(self.brightness_ramp_type)

        self.ramp_type_changed()

    def ramp_type_changed(self) -> None:
        ramp_type = self.cb_ramp_type.currentIndex()

        if ramp_type == RampType.LINEAR:
            self.sb_ramp_log_curvature.setVisible(False)
            self.sb_ramp_powerlaw_exponent.setVisible(False)

        if ramp_type == RampType.LOG:
            self.sb_ramp_log_curvature.setVisible(True)
            self.sb_ramp_powerlaw_exponent.setVisible(False)

        if ramp_type == RampType.POWER_LAW:
            self.sb_ramp_log_curvature.setVisible(False)
            self.sb_ramp_powerlaw_exponent.setVisible(True)

        self.state_changed.emit()

    def layout_components(self) -> None:
        
        super().layout_components()

        ramp_layout = QVBoxLayout()
        ramp_layout.addWidget(self.sb_ramp_duration_sec)
        ramp_layout.addWidget(self.sb_ramp_log_curvature)
        ramp_layout.addWidget(self.sb_ramp_powerlaw_exponent)
        ramp_layout.addWidget(self.cb_ramp_type)
        ramp_layout.addStretch()

        self.ramp_group = QGroupBox('Brightness ramp parameters')
        self.ramp_group.setLayout(ramp_layout)

        self.main_layout.addWidget(self.ramp_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:

        state = super().get_state()
        state['brightness_ramp_duration_sec'] = self.sb_ramp_duration_sec.value()
        state['brightness_ramp_log_curvature'] = self.sb_ramp_log_curvature.value()
        state['brightness_ramp_powerlaw_exponent'] = self.sb_ramp_powerlaw_exponent.value()
        state['brightness_ramp_type'] = self.cb_ramp_type.currentIndex()
        return state
    
    def set_state(self, state: Dict) -> None:

        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'brightness_ramp_duration_sec',
            setter = self.sb_ramp_duration_sec.setValue,
            default = self.brightness_ramp_duration_sec,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'brightness_ramp_log_curvature',
            setter = self.sb_ramp_log_curvature.setValue,
            default = self.brightness_ramp_log_curvature,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'brightness_ramp_powerlaw_exponent',
            setter = self.sb_ramp_powerlaw_exponent.setValue,
            default = self.brightness_ramp_powerlaw_exponent,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'brightness_ramp_type',
            setter = self.cb_ramp_type.setCurrentIndex,
            default = self.brightness_ramp_type
        )

    def from_protocol_item(self, protocol_item: Ramp) -> None:

        super().from_protocol_item(protocol_item)

        self.sb_ramp_duration_sec.setValue(protocol_item.brightness_ramp_duration_sec)
        self.sb_ramp_log_curvature.setValue(protocol_item.brightness_ramp_log_curvature)
        self.sb_ramp_powerlaw_exponent.setValue(protocol_item.brightness_ramp_powerlaw_exponent)
        self.cb_ramp_type.setCurrentIndex(protocol_item.brightness_ramp_type)

    def to_protocol_item(self) -> Ramp:

        protocol = Ramp(
            brightness_ramp_duration_sec = self.sb_ramp_duration_sec.value(),
            brightness_ramp_log_curvature = self.sb_ramp_log_curvature.value(),
            brightness_ramp_powerlaw_exponent = self.sb_ramp_powerlaw_exponent.value(),
            brightness_ramp_type = RampType(self.cb_ramp_type.currentIndex()),
            stop_condition = self.stop_widget.to_stop_condition()
        )
        return protocol

if __name__ == '__main__':

    app = QApplication([])
    window = RampWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
    
