from ZebVR.protocol import (
    Stim, 
    ProtocolItem, 
    VisualProtocolItem,
    VisualProtocolItemWidget, 
    StopWidget, 
    Debouncer,
    PreyCaptureType,
    PeriodicFunction
)
from typing import Dict
from qt_widgets import LabeledDoubleSpinBox, LabeledSpinBox, LabeledComboBox
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
            prey_capture_type: PreyCaptureType = DEFAULT['prey_capture_type'],
            n_preys: int = DEFAULT['n_preys'],
            prey_speed_mm_s: float = DEFAULT['prey_speed_mm_s'],
            prey_speed_deg_s: float = DEFAULT['prey_speed_deg_s'],
            prey_radius_mm: float = DEFAULT['prey_radius_mm'],
            prey_trajectory_radius_mm: float = DEFAULT['prey_trajectory_radius_mm'],
            prey_arc_start_deg: float = DEFAULT['prey_arc_start_deg'],
            prey_arc_stop_deg: float = DEFAULT['prey_arc_stop_deg'],
            prey_arc_phase_deg: float = DEFAULT['prey_arc_phase_deg'],
            prey_periodic_function: PeriodicFunction = DEFAULT['prey_periodic_function'],
            *args,
            **kwargs   
        ) -> None:

        super().__init__(*args, **kwargs)
        self.prey_capture_type = prey_capture_type
        self.n_preys = n_preys
        self.prey_speed_mm_s = prey_speed_mm_s 
        self.prey_speed_deg_s = prey_speed_deg_s 
        self.prey_radius_mm = prey_radius_mm
        self.prey_trajectory_radius_mm = prey_trajectory_radius_mm
        self.prey_arc_start_deg = prey_arc_start_deg
        self.prey_arc_stop_deg = prey_arc_stop_deg
        self.prey_arc_phase_deg = prey_arc_phase_deg
        self.prey_periodic_function = prey_periodic_function

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'prey_capture_type': self.prey_capture_type,
            'n_preys': self.n_preys,
            'prey_speed_mm_s': self.prey_speed_mm_s,
            'prey_speed_deg_s': self.prey_speed_deg_s,
            'prey_radius_mm': self.prey_radius_mm,
            'prey_trajectory_radius_mm': self.prey_trajectory_radius_mm,
            'prey_arc_start_deg': self.prey_arc_start_deg,
            'prey_arc_stop_deg': self.prey_arc_stop_deg,
            'prey_arc_phase_deg': self.prey_arc_phase_deg,
            'prey_periodic_function': self.prey_periodic_function,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'coordinate_sytem': self.coordinate_system,
        }
        return command 
    
class PreyCaptureWidget(VisualProtocolItemWidget):

    def __init__(
            self,
            prey_capture_type: PreyCaptureType = DEFAULT['prey_capture_type'],
            n_preys: int = DEFAULT['n_preys'],
            prey_speed_mm_s: float = DEFAULT['prey_speed_mm_s'],
            prey_speed_deg_s: float = DEFAULT['prey_speed_deg_s'],
            prey_radius_mm: float = DEFAULT['prey_radius_mm'],
            prey_trajectory_radius_mm: float = DEFAULT['prey_trajectory_radius_mm'],
            prey_arc_start_deg: float = DEFAULT['prey_arc_start_deg'],
            prey_arc_stop_deg: float = DEFAULT['prey_arc_stop_deg'],
            prey_arc_phase_deg: float = DEFAULT['prey_arc_phase_deg'],
            prey_periodic_function: PeriodicFunction = DEFAULT['prey_periodic_function'],
            *args, 
            **kwargs
        ) -> None:

        self.prey_capture_type = prey_capture_type
        self.n_preys = n_preys
        self.prey_speed_mm_s = prey_speed_mm_s
        self.prey_speed_deg_s = prey_speed_deg_s
        self.prey_radius_mm = prey_radius_mm
        self.prey_trajectory_radius_mm = prey_trajectory_radius_mm
        self.prey_arc_start_deg = prey_arc_start_deg
        self.prey_arc_stop_deg = prey_arc_stop_deg
        self.prey_arc_phase_deg = prey_arc_phase_deg
        self.prey_periodic_function = prey_periodic_function

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.cb_prey_capture_type = LabeledComboBox()
        self.cb_prey_capture_type.setText('Prey capture type')
        for prey_capture_type in PreyCaptureType:
            self.cb_prey_capture_type.addItem(str(prey_capture_type))
        self.cb_prey_capture_type.setCurrentIndex(self.prey_capture_type)
        self.cb_prey_capture_type.currentIndexChanged.connect(self.prey_capture_type_changed)
        
        self.cb_prey_periodic_function = LabeledComboBox()
        self.cb_prey_periodic_function.setText('Periodic function')
        for periodic_function in PeriodicFunction:
            self.cb_prey_periodic_function.addItem(str(periodic_function))
        self.cb_prey_periodic_function.setCurrentIndex(self.prey_periodic_function)
        self.cb_prey_periodic_function.currentIndexChanged.connect(self.state_changed)

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

        self.sb_prey_speed_deg_s = LabeledDoubleSpinBox()
        self.sb_prey_speed_deg_s.setText('speed (deg/s)')
        self.sb_prey_speed_deg_s.setRange(-360,360)
        self.sb_prey_speed_deg_s.setValue(self.prey_speed_deg_s)
        self.sb_prey_speed_deg_s.valueChanged.connect(self.state_changed)

        self.sb_prey_radius_mm = LabeledDoubleSpinBox()
        self.sb_prey_radius_mm.setText('radius (mm)')
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
        
        self.sb_prey_arc_start_deg = LabeledDoubleSpinBox()
        self.sb_prey_arc_start_deg.setText('angle start (deg)')
        self.sb_prey_arc_start_deg.setRange(-360,360)
        self.sb_prey_arc_start_deg.setValue(self.prey_arc_start_deg)
        self.sb_prey_arc_start_deg.valueChanged.connect(self.state_changed)

        self.sb_prey_arc_stop_deg = LabeledDoubleSpinBox()
        self.sb_prey_arc_stop_deg.setText('angle stop (deg)')
        self.sb_prey_arc_stop_deg.setRange(-360,360)
        self.sb_prey_arc_stop_deg.setValue(self.prey_arc_stop_deg)
        self.sb_prey_arc_stop_deg.valueChanged.connect(self.state_changed)

        self.sb_prey_arc_phase_deg = LabeledDoubleSpinBox()
        self.sb_prey_arc_phase_deg.setText('start phase (deg)')
        self.sb_prey_arc_phase_deg.setRange(0,360)
        self.sb_prey_arc_phase_deg.setValue(self.prey_arc_phase_deg)
        self.sb_prey_arc_phase_deg.valueChanged.connect(self.state_changed)
        
        self.prey_capture_type_changed()

    def layout_components(self) -> None:
        
        super().layout_components()

        preycapture_layout = QVBoxLayout()
        preycapture_layout.addWidget(self.cb_prey_capture_type)
        preycapture_layout.addWidget(self.cb_prey_periodic_function)
        preycapture_layout.addWidget(self.sb_n_preys)
        preycapture_layout.addWidget(self.sb_prey_speed_mm_s)
        preycapture_layout.addWidget(self.sb_prey_speed_deg_s)
        preycapture_layout.addWidget(self.sb_prey_radius_mm)
        preycapture_layout.addWidget(self.sb_trajectory_prey_radius_mm)
        preycapture_layout.addWidget(self.sb_prey_arc_start_deg)
        preycapture_layout.addWidget(self.sb_prey_arc_stop_deg)
        preycapture_layout.addWidget(self.sb_prey_arc_phase_deg)
        preycapture_layout.addStretch()

        self.preycapture_group = QGroupBox('Prey capture parameters')
        self.preycapture_group.setLayout(preycapture_layout)

        self.main_layout.addWidget(self.preycapture_group)
        self.main_layout.addWidget(self.stop_widget)

    def prey_capture_type_changed(self):

        prey_capture_type = PreyCaptureType(self.cb_prey_capture_type.currentIndex())

        if prey_capture_type == PreyCaptureType.RANDOM_CLOUD:
            self.sb_n_preys.setVisible(True)
            self.cb_prey_periodic_function.setVisible(False)
            self.sb_prey_speed_mm_s.setVisible(True)
            self.sb_prey_speed_deg_s.setVisible(False)
            self.sb_trajectory_prey_radius_mm.setVisible(False)
            self.sb_prey_arc_start_deg.setVisible(False)
            self.sb_prey_arc_stop_deg.setVisible(False)  
            self.sb_prey_arc_phase_deg.setVisible(False)  

        if prey_capture_type == PreyCaptureType.RING:
            self.sb_n_preys.setVisible(True)
            self.cb_prey_periodic_function.setVisible(False)
            self.sb_prey_speed_mm_s.setVisible(False)
            self.sb_prey_speed_deg_s.setVisible(True)
            self.sb_trajectory_prey_radius_mm.setVisible(True)    
            self.sb_prey_arc_start_deg.setVisible(False)
            self.sb_prey_arc_stop_deg.setVisible(False)
            self.sb_prey_arc_phase_deg.setVisible(False)

        if prey_capture_type == PreyCaptureType.ARC:
            self.sb_n_preys.setVisible(False)
            self.cb_prey_periodic_function.setVisible(True)
            self.sb_prey_speed_mm_s.setVisible(False)
            self.sb_prey_speed_deg_s.setVisible(True)
            self.sb_trajectory_prey_radius_mm.setVisible(True) 
            self.sb_prey_arc_start_deg.setVisible(True)
            self.sb_prey_arc_stop_deg.setVisible(True)
            self.sb_prey_arc_phase_deg.setVisible(True)

        self.state_changed.emit()

    def get_state(self) -> Dict:
        
        state = super().get_state()
        state['prey_capture_type'] = self.cb_prey_capture_type.currentIndex()
        state['prey_periodic_function'] = self.cb_prey_periodic_function.currentIndex()
        state['n_preys'] = self.sb_n_preys.value()
        state['prey_speed_mm_s'] = self.sb_prey_speed_mm_s.value()
        state['prey_speed_deg_s'] = self.sb_prey_speed_deg_s.value()
        state['prey_radius_mm'] = self.sb_prey_radius_mm.value()
        state['prey_trajectory_radius_mm'] = self.sb_trajectory_prey_radius_mm.value()
        state['prey_arc_start_deg'] = self.sb_prey_arc_start_deg.value()
        state['prey_arc_stop_deg'] = self.sb_prey_arc_stop_deg.value()
        state['prey_arc_phase_deg'] = self.sb_prey_arc_phase_deg.value()
        return state
    
    def set_state(self, state: Dict) -> None:
        
        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'prey_capture_type',
            setter = self.cb_prey_capture_type.setCurrentIndex,
            default = self.prey_capture_type
        )
        set_from_dict(
            dictionary = state,
            key = 'prey_periodic_function',
            setter = self.cb_prey_periodic_function.setCurrentIndex,
            default = self.prey_periodic_function
        )
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
        set_from_dict(
            dictionary = state,
            key = 'prey_arc_start_deg',
            setter = self.sb_prey_arc_start_deg.setValue,
            default = self.prey_arc_start_deg,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'prey_arc_stop_deg',
            setter = self.sb_prey_arc_stop_deg.setValue,
            default = self.prey_arc_stop_deg,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'prey_arc_phase_deg',
            setter = self.sb_prey_arc_phase_deg.setValue,
            default = self.prey_arc_phase_deg,
            cast = float
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:

        super().from_protocol_item(protocol_item)

        if isinstance(protocol_item, PreyCapture):

            self.cb_prey_capture_type.setCurrentIndex(
                getattr(protocol_item, "prey_capture_type", DEFAULT['prey_capture_type'])
            )
            self.cb_prey_periodic_function.setCurrentIndex(
                getattr(protocol_item, "prey_periodic_function", DEFAULT['prey_periodic_function'])
            )
            self.sb_n_preys.setValue(
                getattr(protocol_item, "n_preys", DEFAULT['n_preys'])
            )
            self.sb_prey_speed_mm_s.setValue(
                getattr(protocol_item, "prey_speed_mm_s", DEFAULT['prey_speed_mm_s'])
            )
            self.sb_prey_speed_deg_s.setValue(
                getattr(protocol_item, "prey_speed_deg_s", DEFAULT['prey_speed_deg_s'])
            )
            self.sb_prey_radius_mm.setValue(
                getattr(protocol_item, "prey_radius_mm", DEFAULT['prey_radius_mm'])
            )
            self.sb_trajectory_prey_radius_mm.setValue(
                getattr(protocol_item, "prey_trajectory_radius_mm", DEFAULT['prey_trajectory_radius_mm'])
            )
            self.sb_prey_arc_start_deg.setValue(
                getattr(protocol_item, "prey_arc_start_deg", DEFAULT['prey_arc_start_deg'])
            )
            self.sb_prey_arc_stop_deg.setValue(
                getattr(protocol_item, "prey_arc_stop_deg", DEFAULT['prey_arc_stop_deg'])
            )
            self.sb_prey_arc_phase_deg.setValue(
                getattr(protocol_item, "prey_arc_phase_deg", DEFAULT['prey_arc_phase_deg'])
            )
        
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
        coordinate_system = self.cb_coordinate_system.currentIndex()

        protocol = PreyCapture(
            foreground_color = foreground_color,
            background_color = background_color,
            coordinate_system = coordinate_system,
            prey_capture_type = PreyCaptureType(self.cb_prey_capture_type.currentIndex()),
            prey_periodic_function = PeriodicFunction(self.cb_prey_periodic_function.currentIndex()),
            n_preys = self.sb_n_preys.value(),
            prey_speed_mm_s = self.sb_prey_speed_mm_s.value(),
            prey_speed_deg_s = self.sb_prey_speed_deg_s.value(),
            prey_radius_mm = self.sb_prey_radius_mm.value(),
            prey_trajectory_radius_mm = self.sb_trajectory_prey_radius_mm.value(),
            prey_arc_start_deg = self.sb_prey_arc_start_deg.value(),
            prey_arc_stop_deg = self.sb_prey_arc_stop_deg.value(),
            prey_arc_phase_deg = self.sb_prey_arc_phase_deg.value(),
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
 
