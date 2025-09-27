from ZebVR.protocol import (
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
from ZebVR.utils import set_from_dict
from ZebVR import MAX_PREY
from ..default import DEFAULT

class PreyCapture(VisualProtocolItem):

    STIM_SELECT = Stim.PREY_CAPTURE

    def __init__(
            self,
            n_preys: int = DEFAULT['n_preys'],
            prey_speed_mm_s: float = DEFAULT['prey_speed_mm_s'],
            prey_radius_mm: float = DEFAULT['prey_radius_mm'],
            *args,
            **kwargs   
        ) -> None:

        super().__init__(*args, **kwargs)
        self.n_preys = n_preys
        self.prey_speed_mm_s = prey_speed_mm_s 
        self.prey_radius_mm = prey_radius_mm

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'n_preys': self.n_preys,
            'prey_speed_mm_s': self.prey_speed_mm_s,
            'prey_radius_mm': self.prey_radius_mm
        }
        return command 

class FollowingPreyCapture(VisualProtocolItem):

    STIM_SELECT = Stim.PREY_CAPTURE_CLOSED_LOOP

    def __init__(
            self,
            n_preys: int = DEFAULT['n_preys'],
            prey_speed_deg_s: float = DEFAULT['prey_speed_deg_s'],
            prey_radius_mm: float = DEFAULT['prey_radius_mm'],
            prey_trajectory_radius_mm: float = DEFAULT['prey_trajectory_radius_mm'],
            *args,
            **kwargs   
        ) -> None:

        super().__init__(*args, **kwargs)
        self.n_preys = n_preys
        self.prey_speed_deg_s = prey_speed_deg_s 
        self.prey_radius_mm = prey_radius_mm
        self.prey_trajectory_radius_mm = prey_trajectory_radius_mm

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'n_preys': self.n_preys,
            'prey_speed_deg_s': self.prey_speed_deg_s,
            'prey_radius_mm': self.prey_radius_mm,
            'prey_trajectory_radius_mm': self.prey_trajectory_radius_mm
        }
        return command 
    
class PreyCaptureWidget(VisualProtocolItemWidget):

    def __init__(
            self,
            n_preys: int = DEFAULT['n_preys'],
            prey_speed_mm_s: float = DEFAULT['prey_speed_mm_s'],
            prey_radius_mm: float = DEFAULT['prey_radius_mm'],
            *args, 
            **kwargs
        ) -> None:

        self.n_preys = n_preys
        self.prey_speed_mm_s = prey_speed_mm_s
        self.prey_radius_mm = prey_radius_mm
        
        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.sb_n_preys = LabeledSpinBox()
        self.sb_n_preys.setText('# preys')
        self.sb_n_preys.setRange(0, MAX_PREY) 
        self.sb_n_preys.setValue(self.n_preys)
        self.sb_n_preys.valueChanged.connect(self.state_changed)

        self.sb_prey_speed_mm_s = LabeledDoubleSpinBox()
        self.sb_prey_speed_mm_s.setText('speed (mm/s)')
        self.sb_prey_speed_mm_s.setRange(0,10)
        self.sb_prey_speed_mm_s.setSingleStep(0.025)
        self.sb_prey_speed_mm_s.setValue(self.prey_speed_mm_s)
        self.sb_prey_speed_mm_s.valueChanged.connect(self.state_changed)

        self.sb_prey_radius_mm = LabeledDoubleSpinBox()
        self.sb_prey_radius_mm.setText('radius (mm)')
        self.sb_prey_radius_mm.setSingleStep(0.025)
        self.sb_prey_radius_mm.setRange(0,10)
        self.sb_prey_radius_mm.setValue(self.prey_radius_mm)
        self.sb_prey_radius_mm.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:
        
        super().layout_components()

        preycapture_layout = QVBoxLayout()
        preycapture_layout.addWidget(self.sb_n_preys)
        preycapture_layout.addWidget(self.sb_prey_speed_mm_s)
        preycapture_layout.addWidget(self.sb_prey_radius_mm)
        preycapture_layout.addStretch()

        self.preycapture_group = QGroupBox('Prey capture parameters')
        self.preycapture_group.setLayout(preycapture_layout)

        self.main_layout.addWidget(self.preycapture_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:
        
        state = super().get_state()
        state['n_preys'] = self.sb_n_preys.value()
        state['prey_speed_mm_s'] = self.sb_prey_speed_mm_s.value()
        state['prey_radius_mm'] = self.sb_prey_radius_mm.value()
        return state
    
    def set_state(self, state: Dict) -> None:
        
        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'n_preys',
            setter = self.sb_n_preys.setValue,
            default = self.n_preys,
            cast = int
        )
        set_from_dict(
            dictionary = state,
            key = 'prey_speed_mm_s',
            setter = self.sb_prey_speed_mm_s.setValue,
            default = self.prey_speed_mm_s,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'prey_radius_mm',
            setter = self.sb_prey_radius_mm.setValue,
            default = self.prey_radius_mm,
            cast = float
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:

        super().from_protocol_item(protocol_item)

        if isinstance(protocol_item, PreyCapture):
            self.sb_n_preys.setValue(protocol_item.n_preys)
            self.sb_prey_speed_mm_s.setValue(protocol_item.prey_speed_mm_s)
            self.sb_prey_radius_mm.setValue(protocol_item.prey_radius_mm)
        
    def to_protocol_item(self) -> PreyCapture:
        
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
        protocol = PreyCapture(
            foreground_color = foreground_color,
            background_color = background_color,
            n_preys = self.sb_n_preys.value(),
            prey_speed_mm_s = self.sb_prey_speed_mm_s.value(),
            prey_radius_mm = self.sb_prey_radius_mm.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )
        return protocol

class FollowingPreyCaptureWidget(VisualProtocolItemWidget):

    def __init__(
            self,
            n_preys: int = DEFAULT['n_preys'],
            prey_speed_deg_s: float = DEFAULT['prey_speed_deg_s'],
            prey_radius_mm: float = DEFAULT['prey_radius_mm'],
            prey_trajectory_radius_mm: float = DEFAULT['prey_trajectory_radius_mm'],
            *args, 
            **kwargs
        ) -> None:

        self.n_preys = n_preys
        self.prey_speed_deg_s = prey_speed_deg_s
        self.prey_radius_mm = prey_radius_mm
        self.prey_trajectory_radius_mm = prey_trajectory_radius_mm
        
        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.sb_n_preys = LabeledSpinBox()
        self.sb_n_preys.setText('# preys')
        self.sb_n_preys.setRange(0, MAX_PREY) 
        self.sb_n_preys.setValue(self.n_preys)
        self.sb_n_preys.valueChanged.connect(self.state_changed)

        self.sb_prey_speed_deg_s = LabeledDoubleSpinBox()
        self.sb_prey_speed_deg_s.setText('speed (deg/s)')
        self.sb_prey_speed_deg_s.setRange(-360,360)
        self.sb_prey_speed_deg_s.setSingleStep(1)
        self.sb_prey_speed_deg_s.setValue(self.prey_speed_deg_s)
        self.sb_prey_speed_deg_s.valueChanged.connect(self.state_changed)

        self.sb_prey_radius_mm = LabeledDoubleSpinBox()
        self.sb_prey_radius_mm.setText('prey radius (mm)')
        self.sb_prey_radius_mm.setSingleStep(0.025)
        self.sb_prey_radius_mm.setRange(0,10)
        self.sb_prey_radius_mm.setValue(self.prey_radius_mm)
        self.sb_prey_radius_mm.valueChanged.connect(self.state_changed)

        self.sb_trajectory_prey_radius_mm = LabeledDoubleSpinBox()
        self.sb_trajectory_prey_radius_mm.setText('prey trajectory radius (mm)')
        self.sb_trajectory_prey_radius_mm.setSingleStep(0.025)
        self.sb_trajectory_prey_radius_mm.setRange(0,30)
        self.sb_trajectory_prey_radius_mm.setValue(self.prey_trajectory_radius_mm)
        self.sb_trajectory_prey_radius_mm.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:
        
        super().layout_components()

        preycapture_layout = QVBoxLayout()
        preycapture_layout.addWidget(self.sb_n_preys)
        preycapture_layout.addWidget(self.sb_prey_speed_deg_s)
        preycapture_layout.addWidget(self.sb_prey_radius_mm)
        preycapture_layout.addWidget(self.sb_trajectory_prey_radius_mm)
        preycapture_layout.addStretch()

        self.preycapture_group = QGroupBox('Prey capture parameters')
        self.preycapture_group.setLayout(preycapture_layout)

        self.main_layout.addWidget(self.preycapture_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:
        
        state = super().get_state()
        state['n_preys'] = self.sb_n_preys.value()
        state['prey_speed_deg_s'] = self.sb_prey_speed_deg_s.value()
        state['prey_radius_mm'] = self.sb_prey_radius_mm.value()
        state['prey_trajectory_radius_mm'] = self.sb_trajectory_prey_radius_mm.value()
        return state
    
    def set_state(self, state: Dict) -> None:
        
        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'n_preys',
            setter = self.sb_n_preys.setValue,
            default = self.n_preys,
            cast = int
        )
        set_from_dict(
            dictionary = state,
            key = 'prey_speed_deg_s',
            setter = self.sb_prey_speed_deg_s.setValue,
            default = self.prey_speed_deg_s,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'prey_radius_mm',
            setter = self.sb_prey_radius_mm.setValue,
            default = self.prey_radius_mm,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'prey_trajectory_radius_mm',
            setter = self.sb_trajectory_prey_radius_mm.setValue,
            default = self.prey_trajectory_radius_mm,
            cast = float
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:

        super().from_protocol_item(protocol_item)

        if isinstance(protocol_item, FollowingPreyCapture):
            self.sb_n_preys.setValue(protocol_item.n_preys)
            self.sb_prey_speed_deg_s.setValue(protocol_item.prey_speed_deg_s)
            self.sb_prey_radius_mm.setValue(protocol_item.prey_radius_mm)
            self.sb_trajectory_prey_radius_mm.setValue(protocol_item.prey_trajectory_radius_mm)
        
    def to_protocol_item(self) -> FollowingPreyCapture:
        
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
        protocol = FollowingPreyCapture(
            foreground_color = foreground_color,
            background_color = background_color,
            n_preys = self.sb_n_preys.value(),
            prey_speed_mm_s = self.sb_prey_speed_deg_s.value(),
            prey_radius_mm = self.sb_prey_radius_mm.value(),
            prey_trajectory_radius_mm = self.sb_trajectory_prey_radius_mm.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )
        return protocol
    
if __name__ == '__main__':

    app = QApplication([])
    window = PreyCaptureWidget(
        n_preys = 50,
        prey_speed_mm_s = 0.75,
        prey_radius_mm = 0.25,
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
 
