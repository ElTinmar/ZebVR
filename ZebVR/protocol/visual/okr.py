from ...protocol import Stim, ProtocolItem, VisualProtocolItemWidget, StopWidget, Debouncer
from typing import Tuple, Dict
from qt_widgets import LabeledDoubleSpinBox
from PyQt5.QtWidgets import (
    QGroupBox, 
    QVBoxLayout,
    QApplication, 
)
from ...utils import set_from_dict
from .default import DEFAULT

class OKR(ProtocolItem):

    STIM_SELECT = Stim.Visual.OKR

    def __init__(
            self, 
            okr_spatial_frequency_deg: float = DEFAULT['okr_spatial_frequency_deg'],
            okr_speed_deg_per_sec: float = DEFAULT['okr_speed_deg_per_sec'],
            foreground_color: Tuple[float, float, float, float] = DEFAULT['foreground_color'],
            background_color: Tuple[float, float, float, float] = DEFAULT['background_color'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.okr_spatial_frequency_deg = okr_spatial_frequency_deg
        self.okr_speed_deg_per_sec = okr_speed_deg_per_sec
        self.foreground_color = foreground_color
        self.background_color = background_color 

    def start(self) -> Dict:

        super().start()

        command = {
            'stim_select': self.STIM_SELECT,
            'okr_spatial_frequency_deg': self.okr_spatial_frequency_deg,
            'okr_speed_deg_per_sec': self.okr_speed_deg_per_sec,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color
        }
        return command
    
class OKR_Widget(VisualProtocolItemWidget):

    def __init__(
            self,
            okr_spatial_frequency_deg: float = DEFAULT['okr_spatial_frequency_deg'],
            okr_speed_deg_per_sec: float = DEFAULT['okr_speed_deg_per_sec'],
            *args, 
            **kwargs
        ) -> None:

        self.okr_spatial_frequency_deg = okr_spatial_frequency_deg
        self.okr_speed_deg_per_sec = okr_speed_deg_per_sec
        
        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.sb_okr_spatial_freq = LabeledDoubleSpinBox()
        self.sb_okr_spatial_freq.setText('Spatial frequence (deg)')
        self.sb_okr_spatial_freq.setRange(0,10_000)
        self.sb_okr_spatial_freq.setValue(self.okr_spatial_frequency_deg)
        self.sb_okr_spatial_freq.valueChanged.connect(self.state_changed)

        self.sb_okr_speed = LabeledDoubleSpinBox()
        self.sb_okr_speed.setText('speed (deg/s)')
        self.sb_okr_speed.setRange(-10_000,10_000)
        self.sb_okr_speed.setValue(self.okr_speed_deg_per_sec)
        self.sb_okr_speed.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:
        
        super().layout_components()

        okr_layout = QVBoxLayout()
        okr_layout.addWidget(self.sb_okr_spatial_freq)
        okr_layout.addWidget(self.sb_okr_speed)
        okr_layout.addStretch()

        self.okr_group = QGroupBox('OKR parameters')
        self.okr_group.setLayout(okr_layout)

        self.main_layout.addWidget(self.okr_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:
        
        state = super().get_state()
        state['okr_spatial_frequency_deg'] = self.sb_okr_spatial_freq.value()
        state['okr_speed_deg_per_sec'] = self.sb_okr_speed.value()
        return state
    
    def set_state(self, state: Dict) -> None:
        
        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'okr_spatial_frequency_deg',
            setter = self.sb_okr_spatial_freq.setValue,
            default = self.okr_spatial_frequency_deg,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'okr_speed_deg_per_sec',
            setter = self.sb_okr_speed.setValue,
            default = self.okr_speed_deg_per_sec,
            cast = float
        )

    def from_protocol_item(self, protocol_item: OKR) -> None:

        super().from_protocol_item(protocol_item)

        self.sb_okr_spatial_freq.setValue(protocol_item.okr_spatial_frequency_deg)
        self.sb_okr_speed.setValue(protocol_item.okr_speed_deg_per_sec)

    def to_protocol_item(self) -> OKR:
        
        foreground_color = (
            self.sb_foreground_color_R.value(), 
            self.sb_foreground_color_G.value(),
            self.sb_foreground_color_B.value(),
            self.sb_foreground_color_A.value()
        )
        background_color = (
            self.sb_background_color_R.value(), 
            self.sb_background_color_G.value(),
            self.sb_background_color_B.value(),
            self.sb_background_color_A.value()
        )
        protocol = OKR(
            foreground_color = foreground_color,
            background_color = background_color,
            okr_spatial_frequency_deg = self.sb_okr_spatial_freq.value(),
            okr_speed_deg_per_sec = self.sb_okr_speed.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )
        return protocol
    
if __name__ == '__main__':

    app = QApplication([])
    window = OKR_Widget(
        okr_spatial_frequency_deg = 20,
        okr_speed_deg_per_sec = 36,
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
 
