from ...protocol import (
    Stim, 
    ProtocolItem,
    VisualProtocolItem, 
    VisualProtocolItemWidget, 
    StopWidget, 
    Debouncer
)
from typing import Any, Dict
from qt_widgets import LabeledDoubleSpinBox
from qtpy.QtWidgets import (
    QGroupBox, 
    QVBoxLayout,
    QApplication, 
)
from ...utils import set_from_dict
from ..default import DEFAULT

#TODO add control for type of stimulus: sine, sharp edge, texture

class OMR(VisualProtocolItem):
    
    STIM_SELECT = Stim.OMR
    
    def __init__(
            self, 
            omr_spatial_period_mm: float = DEFAULT['omr_spatial_period_mm'],
            omr_angle_deg: float = DEFAULT['omr_angle_deg'],
            omr_speed_mm_per_sec: float = DEFAULT['omr_speed_mm_per_sec'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.omr_spatial_period_mm = omr_spatial_period_mm
        self.omr_angle_deg = omr_angle_deg
        self.omr_speed_mm_per_sec = omr_speed_mm_per_sec
    
    def start(self) -> Dict:

        command = super().start()
        command.update({
            'stim_select': self.STIM_SELECT,
            'omr_spatial_period_mm': self.omr_spatial_period_mm,
            'omr_angle_deg': self.omr_angle_deg,
            'omr_speed_mm_per_sec': self.omr_speed_mm_per_sec
        })
        return command
    
class OMR_Widget(VisualProtocolItemWidget):

    def __init__(
            self,
            omr_spatial_period_mm: float = DEFAULT['omr_spatial_period_mm'],
            omr_angle_deg: float = DEFAULT['omr_angle_deg'],
            omr_speed_mm_per_sec: float = DEFAULT['omr_speed_mm_per_sec'],
            *args, 
            **kwargs
        ) -> None:

        self.omr_spatial_period_mm = omr_spatial_period_mm
        self.omr_angle_deg = omr_angle_deg
        self.omr_speed_mm_per_sec = omr_speed_mm_per_sec
        
        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.sb_omr_spatial_freq = LabeledDoubleSpinBox()
        self.sb_omr_spatial_freq.setText('Spatial period (mm)')
        self.sb_omr_spatial_freq.setRange(0,10_000)
        self.sb_omr_spatial_freq.setValue(self.omr_spatial_period_mm)
        self.sb_omr_spatial_freq.valueChanged.connect(self.state_changed)

        self.sb_omr_angle = LabeledDoubleSpinBox()
        self.sb_omr_angle.setText('Grating angle (deg)')
        self.sb_omr_angle.setRange(-180,180)
        self.sb_omr_angle.setValue(self.omr_angle_deg)
        self.sb_omr_angle.valueChanged.connect(self.state_changed)

        self.sb_omr_speed = LabeledDoubleSpinBox()
        self.sb_omr_speed.setText('Grating speed (mm/s)')
        self.sb_omr_speed.setRange(-10_000,10_000)
        self.sb_omr_speed.setValue(self.omr_speed_mm_per_sec)
        self.sb_omr_speed.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:
        
        super().layout_components()

        omr_layout = QVBoxLayout()
        omr_layout.addWidget(self.sb_omr_spatial_freq)
        omr_layout.addWidget(self.sb_omr_angle)
        omr_layout.addWidget(self.sb_omr_speed)
        omr_layout.addStretch()

        self.omr_group = QGroupBox('OMR parameters')
        self.omr_group.setLayout(omr_layout)

        self.main_layout.addWidget(self.omr_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:
        
        state = super().get_state()
        state['omr_spatial_period_mm'] = self.sb_omr_spatial_freq.value()
        state['omr_angle_deg'] = self.sb_omr_angle.value()
        state['omr_speed_mm_per_sec'] = self.sb_omr_speed.value() 
        return state
    
    def set_state(self, state: Dict) -> None:
        
        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'omr_spatial_period_mm',
            setter = self.sb_omr_spatial_freq.setValue,
            default = self.omr_spatial_period_mm,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'omr_angle_deg',
            setter = self.sb_omr_angle.setValue,
            default = self.omr_angle_deg,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'omr_speed_mm_per_sec',
            setter = self.sb_omr_speed.setValue,
            default = self.omr_speed_mm_per_sec,
            cast = float
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:

        super().from_protocol_item(protocol_item)

        if isinstance(protocol_item, OMR):
            self.sb_omr_spatial_freq.setValue(protocol_item.omr_spatial_period_mm)
            self.sb_omr_angle.setValue(protocol_item.omr_angle_deg)
            self.sb_omr_speed.setValue(protocol_item.omr_speed_mm_per_sec)  

    def _get_protocol_kwargs(self) -> Dict[str, Any]:

        kwargs = super()._get_protocol_kwargs()
        
        kwargs.update({
            'omr_spatial_period_mm': self.sb_omr_spatial_freq.value(),
            'omr_angle_deg': self.sb_omr_angle.value(),
            'omr_speed_mm_per_sec': self.sb_omr_speed.value(),
        })
        return kwargs

    def to_protocol_item(self) -> OMR:
        return OMR(**self._get_protocol_kwargs())
    
if __name__ == '__main__':

    app = QApplication([])
    window = OMR_Widget(
        omr_spatial_period_mm = 10,
        omr_angle_deg = 0,
        omr_speed_mm_per_sec = 10,
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
 
