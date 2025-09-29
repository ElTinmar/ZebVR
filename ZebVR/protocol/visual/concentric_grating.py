from ...protocol import (
    Stim, 
    ProtocolItem, 
    VisualProtocolItem,
    VisualProtocolItemWidget, 
    StopWidget, 
    Debouncer
)
from typing import Tuple, Dict
from qt_widgets import LabeledDoubleSpinBox
from PyQt5.QtWidgets import (
    QGroupBox, 
    QVBoxLayout,
    QApplication, 
)
from ...utils import set_from_dict
from ..default import DEFAULT

class ConcentricGrating(VisualProtocolItem):

    STIM_SELECT = Stim.CONCENTRIC_GRATING

    def __init__(
            self, 
            spatial_period_mm: float = DEFAULT['concentric_spatial_period_mm'],
            speed_mm_per_sec: float = DEFAULT['concentric_speed_mm_per_sec'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.spatial_period_mm = spatial_period_mm
        self.speed_mm_per_sec = speed_mm_per_sec

    def start(self) -> Dict:

        super().start()

        command = {
            'stim_select': self.STIM_SELECT,
            'concentric_spatial_period_mm': self.spatial_period_mm,
            'concentric_speed_mm_per_sec': self.speed_mm_per_sec,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'closed_loop': self.closed_loop
        }
        return command
    
class ConcentricGratingWidget(VisualProtocolItemWidget):

    def __init__(
            self,
            spatial_period_mm: float = DEFAULT['concentric_spatial_period_mm'],
            speed_mm_per_sec: float = DEFAULT['concentric_speed_mm_per_sec'],
            *args, 
            **kwargs
        ) -> None:

        self.spatial_period_mm = spatial_period_mm
        self.speed_mm_per_sec = speed_mm_per_sec
        
        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.chb_closed_loop.setChecked(False)
        self.chb_closed_loop.setVisible(False)

        self.sb_concentric_spatial_freq = LabeledDoubleSpinBox()
        self.sb_concentric_spatial_freq.setText('Spatial period (mm)')
        self.sb_concentric_spatial_freq.setRange(0,10_000)
        self.sb_concentric_spatial_freq.setValue(self.spatial_period_mm)
        self.sb_concentric_spatial_freq.valueChanged.connect(self.state_changed)

        self.sb_concentric_speed = LabeledDoubleSpinBox()
        self.sb_concentric_speed.setText('Grating speed (mm/s)')
        self.sb_concentric_speed.setRange(-10_000,10_000)
        self.sb_concentric_speed.setValue(self.speed_mm_per_sec)
        self.sb_concentric_speed.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:
        
        super().layout_components()

        concentric_layout = QVBoxLayout()
        concentric_layout.addWidget(self.sb_concentric_spatial_freq)
        concentric_layout.addWidget(self.sb_concentric_speed)
        concentric_layout.addStretch()

        self.concentric_group = QGroupBox('Concentric grating parameters')
        self.concentric_group.setLayout(concentric_layout)

        self.main_layout.addWidget(self.concentric_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:
        
        state = super().get_state()
        state['concentric_spatial_period_mm'] = self.sb_concentric_spatial_freq.value()
        state['concentric_speed_mm_per_sec'] = self.sb_concentric_speed.value() 
        return state
    
    def set_state(self, state: Dict) -> None:
        
        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'concentric_spatial_period_mm',
            setter = self.sb_concentric_spatial_freq.setValue,
            default = self.spatial_period_mm,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'concentric_speed_mm_per_sec',
            setter = self.sb_concentric_speed.setValue,
            default = self.speed_mm_per_sec,
            cast = float
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:

        super().from_protocol_item(protocol_item)

        if isinstance(protocol_item, ConcentricGrating):
            self.sb_concentric_spatial_freq.setValue(protocol_item.spatial_period_mm)
            self.sb_concentric_speed.setValue(protocol_item.speed_mm_per_sec)

    def to_protocol_item(self) -> ConcentricGrating:
        
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
        closed_loop = self.chb_closed_loop.isChecked()
        protocol = ConcentricGrating(
            foreground_color = foreground_color,
            background_color = background_color,
            closed_loop = closed_loop,
            spatial_period_mm = self.sb_concentric_spatial_freq.value(),
            speed_mm_per_sec = self.sb_concentric_speed.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )
        return protocol
    
if __name__ == '__main__':

    app = QApplication([])
    window = ConcentricGratingWidget(
        spatial_period_mm = 10,
        speed_mm_per_sec = 10,
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
 
