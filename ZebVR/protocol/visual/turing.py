from ...protocol import (
    Stim, 
    ProtocolItem,
    VisualProtocolItem, 
    VisualProtocolItemWidget, 
    StopWidget, 
    Debouncer
)
from typing import Dict
from qt_widgets import LabeledDoubleSpinBox, LabeledSpinBox
from PyQt5.QtWidgets import (
    QGroupBox, 
    QVBoxLayout,
    QApplication, 
)
from ...utils import set_from_dict
from ..default import DEFAULT

class Turing(VisualProtocolItem):
    
    STIM_SELECT = Stim.TURING
    
    def __init__(
            self, 
            turing_spatial_period_mm: float = DEFAULT['turing_spatial_period_mm'],
            turing_angle_deg: float = DEFAULT['turing_angle_deg'],
            turing_speed_mm_per_sec: float = DEFAULT['turing_speed_mm_per_sec'],
            turing_n_waves: int = DEFAULT['turing_n_waves'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.turing_spatial_period_mm = turing_spatial_period_mm
        self.turing_angle_deg = turing_angle_deg
        self.turing_speed_mm_per_sec = turing_speed_mm_per_sec
        self.turing_n_waves = turing_n_waves
    
    def start(self) -> Dict:

        super().start()

        command = {
            'stim_select': self.STIM_SELECT,
            'turing_spatial_period_mm': self.turing_spatial_period_mm,
            'turing_angle_deg': self.turing_angle_deg,
            'turing_speed_mm_per_sec': self.turing_speed_mm_per_sec,
            'turing_n_waves': self.turing_n_waves,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'coordinate_sytem': self.coordinate_system
        }
        return command
    
class TuringWidget(VisualProtocolItemWidget):

    def __init__(
            self,
            turing_spatial_period_mm: float = DEFAULT['turing_spatial_period_mm'],
            turing_angle_deg: float = DEFAULT['turing_angle_deg'],
            turing_speed_mm_per_sec: float = DEFAULT['turing_speed_mm_per_sec'],
            turing_n_waves: int = DEFAULT['turing_n_waves'],
            *args, 
            **kwargs
        ) -> None:

        self.turing_spatial_period_mm = turing_spatial_period_mm
        self.turing_angle_deg = turing_angle_deg
        self.turing_speed_mm_per_sec = turing_speed_mm_per_sec
        self.turing_n_waves = turing_n_waves
        
        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.sb_turing_spatial_freq = LabeledDoubleSpinBox()
        self.sb_turing_spatial_freq.setText('Spatial period (mm)')
        self.sb_turing_spatial_freq.setRange(0,10_000)
        self.sb_turing_spatial_freq.setValue(self.turing_spatial_period_mm)
        self.sb_turing_spatial_freq.valueChanged.connect(self.state_changed)

        self.sb_turing_angle = LabeledDoubleSpinBox()
        self.sb_turing_angle.setText('Drifting angle (deg)')
        self.sb_turing_angle.setRange(-180,180)
        self.sb_turing_angle.setValue(self.turing_angle_deg)
        self.sb_turing_angle.valueChanged.connect(self.state_changed)

        self.sb_turing_speed = LabeledDoubleSpinBox()
        self.sb_turing_speed.setText('Drifting speed (mm/s)')
        self.sb_turing_speed.setRange(-10_000,10_000)
        self.sb_turing_speed.setValue(self.turing_speed_mm_per_sec)
        self.sb_turing_speed.valueChanged.connect(self.state_changed)

        self.sb_turing_n_waves = LabeledSpinBox()
        self.sb_turing_n_waves.setText('N waves')
        self.sb_turing_n_waves.setRange(1, 1024)
        self.sb_turing_n_waves.setValue(self.turing_n_waves)
        self.sb_turing_n_waves.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:
        
        super().layout_components()

        turing_layout = QVBoxLayout()
        turing_layout.addWidget(self.sb_turing_spatial_freq)
        turing_layout.addWidget(self.sb_turing_angle)
        turing_layout.addWidget(self.sb_turing_speed)
        turing_layout.addWidget(self.sb_turing_n_waves)
        turing_layout.addStretch()

        self.turing_group = QGroupBox('Turing parameters')
        self.turing_group.setLayout(turing_layout)

        self.main_layout.addWidget(self.turing_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:
        
        state = super().get_state()
        state['turing_spatial_period_mm'] = self.sb_turing_spatial_freq.value()
        state['turing_angle_deg'] = self.sb_turing_angle.value()
        state['turing_speed_mm_per_sec'] = self.sb_turing_speed.value() 
        state['turing_n_waves'] = self.sb_turing_n_waves.value() 
        return state
    
    def set_state(self, state: Dict) -> None:
        
        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'turing_spatial_period_mm',
            setter = self.sb_turing_spatial_freq.setValue,
            default = self.turing_spatial_period_mm,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'turing_angle_deg',
            setter = self.sb_turing_angle.setValue,
            default = self.turing_angle_deg,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'turing_speed_mm_per_sec',
            setter = self.sb_turing_speed.setValue,
            default = self.turing_speed_mm_per_sec,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'turing_n_waves',
            setter = self.sb_turing_n_waves.setValue,
            default = self.turing_n_waves,
            cast = int
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:

        super().from_protocol_item(protocol_item)

        if isinstance(protocol_item, Turing):
            self.sb_turing_spatial_freq.setValue(protocol_item.turing_spatial_period_mm)
            self.sb_turing_angle.setValue(protocol_item.turing_angle_deg)
            self.sb_turing_speed.setValue(protocol_item.turing_speed_mm_per_sec) 
            self.sb_turing_n_waves.setValue(protocol_item.turing_n_waves)  

    def to_protocol_item(self) -> Turing:
        
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
        coordinate_system = self.cb_coordinate_system.currentIndex()
        
        protocol = Turing(
            foreground_color = foreground_color,
            background_color = background_color,
            coordinate_system = coordinate_system,
            turing_spatial_period_mm = self.sb_turing_spatial_freq.value(),
            turing_angle_deg = self.sb_turing_angle.value(),
            turing_speed_mm_per_sec = self.sb_turing_speed.value(),
            turing_n_waves = self.sb_turing_n_waves.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )
        return protocol
    
if __name__ == '__main__':

    app = QApplication([])
    window = TuringWidget(
        turing_spatial_period_mm = 10,
        turing_angle_deg = 0,
        turing_speed_mm_per_sec = 10,
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
 
