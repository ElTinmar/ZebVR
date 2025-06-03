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
class Dot(ProtocolItem):

    STIM_SELECT = Stim.Visual.DOT

    def __init__(
            self, 
            foreground_color: Tuple[float, float, float, float] = DEFAULT['foreground_color'],
            background_color: Tuple[float, float, float, float] = DEFAULT['background_color'],
            dot_center_mm: Tuple[float, float] = DEFAULT['dot_center_mm'],
            dot_radius_mm: float = DEFAULT['dot_radius_mm'],
            *args,
            **kwargs   
        ) -> None:

        super().__init__(*args, **kwargs)
        self.foreground_color = foreground_color 
        self.background_color = background_color
        self.dot_center_mm = dot_center_mm
        self.dot_radius_mm = dot_radius_mm 

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'dot_center_mm': self.dot_center_mm,
            'dot_radius_mm': self.dot_radius_mm,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
        }
        return command 

class FollowingDot(Dot):
    STIM_SELECT = Stim.Visual.FOLLOWING_DOT

class DotWidget(VisualProtocolItemWidget):

    group_name: str = 'Dot parameters'

    def __init__(
            self,
            dot_center_mm: Tuple[float, float] = DEFAULT['dot_center_mm'],
            dot_radius_mm: float = DEFAULT['dot_radius_mm'],
            *args, 
            **kwargs
        ) -> None:

        self.dot_center_mm = dot_center_mm
        self.dot_radius_mm = dot_radius_mm

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.sb_dot_center_mm_x = LabeledDoubleSpinBox()
        self.sb_dot_center_mm_x.setText('X (mm)')
        self.sb_dot_center_mm_x.setRange(-10_000,10_000)
        self.sb_dot_center_mm_x.setValue(self.dot_center_mm[0])
        self.sb_dot_center_mm_x.valueChanged.connect(self.state_changed)

        self.sb_dot_center_mm_y = LabeledDoubleSpinBox()
        self.sb_dot_center_mm_y.setText('Y (mm)')
        self.sb_dot_center_mm_y.setRange(-10_000,10_000)
        self.sb_dot_center_mm_y.setValue(self.dot_center_mm[1])
        self.sb_dot_center_mm_y.valueChanged.connect(self.state_changed)

        self.sb_dot_radius_mm = LabeledDoubleSpinBox()
        self.sb_dot_radius_mm.setText('radius (mm)')
        self.sb_dot_radius_mm.setRange(0,100)
        self.sb_dot_radius_mm.setValue(self.dot_radius_mm)
        self.sb_dot_radius_mm.setSingleStep(0.1)
        self.sb_dot_radius_mm.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:
        
        super().layout_components()

        dot_layout = QVBoxLayout()
        dot_layout.addWidget(self.sb_dot_center_mm_x)
        dot_layout.addWidget(self.sb_dot_center_mm_y)
        dot_layout.addWidget(self.sb_dot_radius_mm)
        dot_layout.addStretch()

        self.dot_group = QGroupBox(self.group_name)
        self.dot_group.setLayout(dot_layout)

        self.main_layout.addWidget(self.dot_group)

    def get_state(self) -> Dict:
        
        state = super().get_state()
        state['dot_center_mm'] = (
            self.sb_dot_center_mm_x.value(),
            self.sb_dot_center_mm_y.value()
        )
        state['dot_radius_mm'] = self.sb_dot_radius_mm.value()
        return state
    
    def set_state(self, state: Dict) -> None:
        
        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'dot_center_mm',
            setter = self.sb_dot_center_mm_x.setValue,
            default = self.dot_center_mm,
            cast = lambda x: float(x[0])
        )
        set_from_dict(
            dictionary = state,
            key = 'dot_center_mm',
            setter = self.sb_dot_center_mm_y.setValue,
            default = self.dot_center_mm,
            cast = lambda x: float(x[1])
        )
        set_from_dict(
            dictionary = state,
            key = 'dot_radius_mm',
            setter = self.sb_dot_radius_mm.setValue,
            default = self.dot_radius_mm,
            cast = float
        )

    def from_protocol_item(self, protocol_item: Dot) -> None:

        super().from_protocol_item(protocol_item)

        self.sb_dot_center_mm_x.setValue(protocol_item.dot_center_mm[0])
        self.sb_dot_center_mm_y.setValue(protocol_item.dot_center_mm[1])
        self.sb_dot_radius_mm.setValue(protocol_item.dot_radius_mm)

    def to_protocol_item(self) -> Dot:
        
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
        protocol = Dot(
            foreground_color = foreground_color,
            background_color = background_color,
            dot_center_mm = (
                self.sb_dot_center_mm_x.value(),
                self.sb_dot_center_mm_y.value()
            ),
            dot_radius_mm = self.sb_dot_radius_mm.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )
        return protocol

class FollowingDotWidget(DotWidget):
    
    group_name: str = 'Following dot parameters'

    def to_protocol_item(self) -> FollowingDot:

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
        protocol = FollowingDot(
            foreground_color = foreground_color,
            background_color = background_color,
            dot_center_mm = (
                self.sb_dot_center_mm_x.value(),
                self.sb_dot_center_mm_y.value()
            ),
            dot_radius_mm = self.sb_dot_radius_mm.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )
        return protocol

if __name__ == '__main__':

    app = QApplication([])
    window1 = DotWidget(
        dot_center_mm = (0,0),
        dot_radius_mm = 10,
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window1.show()
    window2 = FollowingDotWidget(
        dot_center_mm = (0,0),
        dot_radius_mm = 10,
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window2.show()
    app.exec()
 

