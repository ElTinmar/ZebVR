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
class Looming(ProtocolItem):

    STIM_SELECT = Stim.Visual.LOOMING

    def __init__(
            self, 
            foreground_color: Tuple[float, float, float, float] = DEFAULT['foreground_color'],
            background_color: Tuple[float, float, float, float] = DEFAULT['background_color'],
            looming_center_mm: Tuple[float, float] = DEFAULT['looming_center_mm'],
            looming_period_sec: float = DEFAULT['looming_period_sec'],
            looming_expansion_time_sec: float = DEFAULT['looming_expansion_time_sec'],
            looming_expansion_speed_mm_per_sec: float = DEFAULT['looming_expansion_speed_mm_per_sec'],
            *args,
            **kwargs   
        ) -> None:

        super().__init__(*args, **kwargs)
        self.foreground_color = foreground_color 
        self.background_color = background_color
        self.looming_center_mm = looming_center_mm
        self.looming_period_sec = looming_period_sec 
        self.looming_expansion_time_sec = looming_expansion_time_sec
        self.looming_expansion_speed_mm_per_sec = looming_expansion_speed_mm_per_sec

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'looming_center_mm': self.looming_center_mm,
            'looming_period_sec': self.looming_period_sec,
            'looming_expansion_time_sec': self.looming_expansion_time_sec,
            'looming_expansion_speed_mm_per_sec': self.looming_expansion_speed_mm_per_sec,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color
        }
        return command 

class FollowingLooming(Looming):
    STIM_SELECT = Stim.Visual.FOLLOWING_LOOMING

class LoomingWidget(VisualProtocolItemWidget):

    group_name: str = 'Looming parameters'

    def __init__(
            self,
            looming_center_mm: Tuple[float, float] = DEFAULT['looming_center_mm'],
            looming_period_sec: float = DEFAULT['looming_period_sec'],
            looming_expansion_time_sec: float = DEFAULT['looming_expansion_time_sec'],
            looming_expansion_speed_mm_per_sec: float = DEFAULT['looming_expansion_speed_mm_per_sec'],
            *args, 
            **kwargs
        ) -> None:

        self.looming_center_mm = looming_center_mm
        self.looming_period_sec = looming_period_sec
        self.looming_expansion_time_sec = looming_expansion_time_sec
        self.looming_expansion_speed_mm_per_sec = looming_expansion_speed_mm_per_sec
        
        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.sb_looming_center_mm_x = LabeledDoubleSpinBox()
        self.sb_looming_center_mm_x.setText('X (mm)')
        self.sb_looming_center_mm_x.setRange(-10_000,10_000)
        self.sb_looming_center_mm_x.setValue(self.looming_center_mm[0])
        self.sb_looming_center_mm_x.valueChanged.connect(self.state_changed)

        self.sb_looming_center_mm_y = LabeledDoubleSpinBox()
        self.sb_looming_center_mm_y.setText('Y (mm)')
        self.sb_looming_center_mm_y.setRange(-10_000,10_000)
        self.sb_looming_center_mm_y.setValue(self.looming_center_mm[1])
        self.sb_looming_center_mm_y.valueChanged.connect(self.state_changed)

        self.sb_looming_period_sec = LabeledDoubleSpinBox()
        self.sb_looming_period_sec.setText('period (s)')
        self.sb_looming_period_sec.setRange(0,100_000)
        self.sb_looming_period_sec.setValue(self.looming_period_sec)
        self.sb_looming_period_sec.valueChanged.connect(self.state_changed)

        self.sb_looming_expansion_time_sec = LabeledDoubleSpinBox()
        self.sb_looming_expansion_time_sec.setText('expansion time (s)')
        self.sb_looming_expansion_time_sec.setRange(0,100_000)
        self.sb_looming_expansion_time_sec.setValue(self.looming_expansion_time_sec)
        self.sb_looming_expansion_time_sec.valueChanged.connect(self.state_changed)

        self.sb_looming_expansion_speed_mm_per_sec = LabeledDoubleSpinBox()
        self.sb_looming_expansion_speed_mm_per_sec.setText('expansion speed (mm/s)')
        self.sb_looming_expansion_speed_mm_per_sec.setRange(0,100_000)
        self.sb_looming_expansion_speed_mm_per_sec.setValue(self.looming_expansion_speed_mm_per_sec)
        self.sb_looming_expansion_speed_mm_per_sec.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:
        
        super().layout_components()

        looming_layout = QVBoxLayout()
        looming_layout.addWidget(self.sb_looming_center_mm_x)
        looming_layout.addWidget(self.sb_looming_center_mm_y)
        looming_layout.addWidget(self.sb_looming_period_sec)
        looming_layout.addWidget(self.sb_looming_expansion_time_sec)
        looming_layout.addWidget(self.sb_looming_expansion_speed_mm_per_sec)
        looming_layout.addStretch()

        self.looming_group = QGroupBox(self.group_name)
        self.looming_group.setLayout(looming_layout)

        self.main_layout.addWidget(self.looming_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:
        
        state = super().get_state()
        state['looming_center_mm'] = (
            self.sb_looming_center_mm_x.value(),
            self.sb_looming_center_mm_y.value()
        )
        state['looming_period_sec'] = self.sb_looming_period_sec.value()
        state['looming_expansion_time_sec'] = self.sb_looming_expansion_time_sec.value()
        state['looming_expansion_speed_mm_per_sec'] = self.sb_looming_expansion_speed_mm_per_sec.value()
        return state
    
    def set_state(self, state: Dict) -> None:
        
        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'looming_center_mm',
            setter = self.sb_looming_center_mm_x.setValue,
            default = self.looming_center_mm,
            cast = lambda x: float(x[0])
        )
        set_from_dict(
            dictionary = state,
            key = 'looming_center_mm',
            setter = self.sb_looming_center_mm_y.setValue,
            default = self.looming_center_mm,
            cast = lambda x: float(x[1])
        )
        set_from_dict(
            dictionary = state,
            key = 'looming_period_sec',
            setter = self.sb_looming_period_sec.setValue,
            default = self.looming_period_sec,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'looming_expansion_time_sec',
            setter = self.sb_looming_expansion_time_sec.setValue,
            default = self.looming_expansion_time_sec,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'looming_expansion_speed_mm_per_sec',
            setter = self.sb_looming_expansion_speed_mm_per_sec.setValue,
            default = self.looming_expansion_speed_mm_per_sec,
            cast = float
        )

    def from_protocol_item(self, protocol_item: Looming) -> None:

        super().from_protocol_item(protocol_item)

        self.sb_looming_center_mm_x.setValue(protocol_item.looming_center_mm[0])
        self.sb_looming_center_mm_y.setValue(protocol_item.looming_center_mm[1])
        self.sb_looming_period_sec.setValue(protocol_item.looming_period_sec)
        self.sb_looming_expansion_time_sec.setValue(protocol_item.looming_expansion_time_sec)
        self.sb_looming_expansion_speed_mm_per_sec.setValue(protocol_item.looming_expansion_speed_mm_per_sec)

    def to_protocol_item(self) -> Looming:
        
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
        protocol = Looming(
            foreground_color = foreground_color,
            background_color = background_color,
            looming_center_mm = (
                self.sb_looming_center_mm_x.value(),
                self.sb_looming_center_mm_y.value()
            ),
            looming_period_sec = self.sb_looming_period_sec.value(),
            looming_expansion_time_sec = self.sb_looming_expansion_time_sec.value(),
            looming_expansion_speed_mm_per_sec = self.sb_looming_expansion_speed_mm_per_sec.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )
        return protocol

class FollowingLoomingWidget(LoomingWidget):
    
    group_name: str = 'Following looming parameters'

    def to_protocol_item(self) -> FollowingLooming:

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
        protocol = FollowingLooming(
            foreground_color = foreground_color,
            background_color = background_color,
            looming_center_mm = (
                self.sb_looming_center_mm_x.value(),
                self.sb_looming_center_mm_y.value()
            ),
            looming_period_sec = self.sb_looming_period_sec.value(),
            looming_expansion_time_sec = self.sb_looming_expansion_time_sec.value(),
            looming_expansion_speed_mm_per_sec = self.sb_looming_expansion_speed_mm_per_sec.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )
        return protocol

if __name__ == '__main__':

    app = QApplication([])
    window1 = LoomingWidget(
        looming_center_mm = (0,0),
        looming_period_sec = 10,
        looming_expansion_time_sec = 10,
        looming_expansion_speed_mm_per_sec = 10,
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window1.show()
    window2 = FollowingLoomingWidget(
        looming_center_mm = (0,0),
        looming_period_sec = 10,
        looming_expansion_time_sec = 10,
        looming_expansion_speed_mm_per_sec = 10,
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window2.show()
    app.exec()
 

