from ...protocol import (
    Stim, 
    ProtocolItem, 
    VisualProtocolItem,
    VisualProtocolItemWidget, 
    StopWidget, 
    Debouncer,
    LoomingType
)
from typing import Tuple, Dict
from qt_widgets import LabeledDoubleSpinBox, LabeledComboBox
from PyQt5.QtWidgets import (
    QGroupBox, 
    QVBoxLayout,
    QApplication, 
)
from ...utils import set_from_dict
from ..default import DEFAULT

class Looming(VisualProtocolItem):

    STIM_SELECT = Stim.LOOMING

    def __init__(
            self, 
            looming_type: LoomingType = DEFAULT['looming_type'],
            looming_center_mm: Tuple[float, float] = DEFAULT['looming_center_mm'],
            looming_period_sec: float = DEFAULT['looming_period_sec'],
            looming_expansion_time_sec: float = DEFAULT['looming_expansion_time_sec'],
            looming_expansion_speed_mm_per_sec: float = DEFAULT['looming_expansion_speed_mm_per_sec'],
            looming_expansion_speed_deg_per_sec: float = DEFAULT['looming_expansion_speed_deg_per_sec'],
            looming_angle_start_deg: float = DEFAULT['looming_angle_start_deg'],
            looming_angle_stop_deg: float = DEFAULT['looming_angle_stop_deg'],
            looming_size_to_speed_ratio_ms: float = DEFAULT['looming_size_to_speed_ratio_ms'],
            *args,
            **kwargs   
        ) -> None:

        super().__init__(*args, **kwargs)
        self.looming_type = looming_type
        self.looming_center_mm = looming_center_mm
        self.looming_period_sec = looming_period_sec 
        self.looming_expansion_time_sec = looming_expansion_time_sec
        self.looming_expansion_speed_mm_per_sec = looming_expansion_speed_mm_per_sec
        self.looming_expansion_speed_deg_per_sec = looming_expansion_speed_deg_per_sec
        self.looming_angle_start_deg = looming_angle_start_deg
        self.looming_angle_stop_deg = looming_angle_stop_deg
        self.looming_size_to_speed_ratio_ms = looming_size_to_speed_ratio_ms

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'looming_type': self.looming_type,
            'looming_center_mm': self.looming_center_mm,
            'looming_period_sec': self.looming_period_sec,
            'looming_expansion_time_sec': self.looming_expansion_time_sec,
            'looming_expansion_speed_mm_per_sec': self.looming_expansion_speed_mm_per_sec,
            'looming_expansion_speed_deg_per_sec': self.looming_expansion_speed_deg_per_sec,
            'looming_angle_start_deg': self.looming_angle_start_deg,
            'looming_angle_stop_deg': self.looming_angle_stop_deg,
            'looming_size_to_speed_ratio_ms': self.looming_size_to_speed_ratio_ms, 
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'closed_loop': self.closed_loop
        }
        return command 

class LoomingWidget(VisualProtocolItemWidget):

    group_name: str = 'Looming parameters'

    def __init__(
            self,
            looming_type: LoomingType = DEFAULT['looming_type'],
            looming_center_mm: Tuple[float, float] = DEFAULT['looming_center_mm'],
            looming_period_sec: float = DEFAULT['looming_period_sec'],
            looming_expansion_time_sec: float = DEFAULT['looming_expansion_time_sec'],
            looming_expansion_speed_mm_per_sec: float = DEFAULT['looming_expansion_speed_mm_per_sec'],
            looming_expansion_speed_deg_per_sec: float = DEFAULT['looming_expansion_speed_deg_per_sec'],
            looming_angle_start_deg: float = DEFAULT['looming_angle_start_deg'],
            looming_angle_stop_deg: float = DEFAULT['looming_angle_stop_deg'],
            looming_size_to_speed_ratio_ms: float = DEFAULT['looming_size_to_speed_ratio_ms'],
            *args, 
            **kwargs
        ) -> None:

        self.looming_type = looming_type
        self.looming_center_mm = looming_center_mm
        self.looming_period_sec = looming_period_sec 
        self.looming_expansion_time_sec = looming_expansion_time_sec
        self.looming_expansion_speed_mm_per_sec = looming_expansion_speed_mm_per_sec
        self.looming_expansion_speed_deg_per_sec = looming_expansion_speed_deg_per_sec
        self.looming_angle_start_deg = looming_angle_start_deg
        self.looming_angle_stop_deg = looming_angle_stop_deg
        self.looming_size_to_speed_ratio_ms = looming_size_to_speed_ratio_ms
        
        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.cb_looming_type = LabeledComboBox()
        self.cb_looming_type.setText('Looming type')
        for looming_type in LoomingType:
            self.cb_looming_type.addItem(str(looming_type))
        self.cb_looming_type.setCurrentIndex(self.looming_type)
        self.cb_looming_type.currentIndexChanged.connect(self.looming_type_changed)

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

        self.sb_looming_expansion_speed_deg_per_sec = LabeledDoubleSpinBox()
        self.sb_looming_expansion_speed_deg_per_sec.setText('expansion speed (deg/s)')
        self.sb_looming_expansion_speed_deg_per_sec.setRange(0,360)
        self.sb_looming_expansion_speed_deg_per_sec.setValue(self.looming_expansion_speed_deg_per_sec)
        self.sb_looming_expansion_speed_deg_per_sec.valueChanged.connect(self.state_changed)

        self.sb_looming_angle_start_deg = LabeledDoubleSpinBox()
        self.sb_looming_angle_start_deg.setText('angle start (deg)')
        self.sb_looming_angle_start_deg.setRange(0,360)
        self.sb_looming_angle_start_deg.setValue(self.looming_angle_start_deg)
        self.sb_looming_angle_start_deg.valueChanged.connect(self.state_changed)

        self.sb_looming_angle_stop_deg = LabeledDoubleSpinBox()
        self.sb_looming_angle_stop_deg.setText('angle stop (deg)')
        self.sb_looming_angle_stop_deg.setRange(0,360)
        self.sb_looming_angle_stop_deg.setValue(self.looming_angle_stop_deg)
        self.sb_looming_angle_stop_deg.valueChanged.connect(self.state_changed)

        self.sb_looming_size_to_speed_ratio = LabeledDoubleSpinBox()
        self.sb_looming_size_to_speed_ratio.setText('l/v (ms)')
        self.sb_looming_size_to_speed_ratio.setRange(0,300)
        self.sb_looming_size_to_speed_ratio.setValue(self.looming_size_to_speed_ratio_ms)
        self.sb_looming_size_to_speed_ratio.valueChanged.connect(self.state_changed)

        self.looming_type_changed()

    def layout_components(self) -> None:
        
        super().layout_components()

        looming_layout = QVBoxLayout()
        looming_layout.addWidget(self.cb_looming_type)
        looming_layout.addWidget(self.sb_looming_center_mm_x)
        looming_layout.addWidget(self.sb_looming_center_mm_y)
        looming_layout.addWidget(self.sb_looming_period_sec)
        looming_layout.addWidget(self.sb_looming_expansion_time_sec)
        looming_layout.addWidget(self.sb_looming_expansion_speed_mm_per_sec)
        looming_layout.addWidget(self.sb_looming_expansion_speed_deg_per_sec)
        looming_layout.addWidget(self.sb_looming_angle_start_deg)
        looming_layout.addWidget(self.sb_looming_angle_stop_deg)
        looming_layout.addWidget(self.sb_looming_size_to_speed_ratio)
        looming_layout.addStretch()

        self.looming_group = QGroupBox(self.group_name)
        self.looming_group.setLayout(looming_layout)

        self.main_layout.addWidget(self.looming_group)
        self.main_layout.addWidget(self.stop_widget)

    def looming_type_changed(self):

        looming_type = LoomingType(self.cb_looming_type.currentIndex())

        if looming_type == LoomingType.LINEAR_RADIUS:
            self.sb_looming_period_sec.setVisible(True)
            self.sb_looming_expansion_time_sec.setVisible(True)
            self.sb_looming_expansion_speed_mm_per_sec.setVisible(True)
            self.sb_looming_expansion_speed_deg_per_sec.setVisible(False)
            self.sb_looming_angle_start_deg.setVisible(False)
            self.sb_looming_angle_stop_deg.setVisible(False)
            self.sb_looming_size_to_speed_ratio.setVisible(False)

        if looming_type == LoomingType.LINEAR_ANGLE:
            self.sb_looming_period_sec.setVisible(True)
            self.sb_looming_expansion_time_sec.setVisible(True)
            self.sb_looming_expansion_speed_mm_per_sec.setVisible(False)
            self.sb_looming_expansion_speed_deg_per_sec.setVisible(True)
            self.sb_looming_angle_start_deg.setVisible(False)
            self.sb_looming_angle_stop_deg.setVisible(False)
            self.sb_looming_size_to_speed_ratio.setVisible(False)

        if looming_type == LoomingType.CONSTANT_VELOCITY:
            self.sb_looming_period_sec.setVisible(False)
            self.sb_looming_expansion_time_sec.setVisible(False)
            self.sb_looming_expansion_speed_mm_per_sec.setVisible(False)
            self.sb_looming_expansion_speed_deg_per_sec.setVisible(False)
            self.sb_looming_angle_start_deg.setVisible(True)
            self.sb_looming_angle_stop_deg.setVisible(True)
            self.sb_looming_size_to_speed_ratio.setVisible(True)

        self.state_changed.emit()

    def get_state(self) -> Dict:
        
        state = super().get_state()
        state['looming_center_mm'] = (
            self.sb_looming_center_mm_x.value(),
            self.sb_looming_center_mm_y.value()
        )
        state['looming_type'] = self.cb_looming_type.currentIndex()
        state['looming_period_sec'] = self.sb_looming_period_sec.value()
        state['looming_expansion_time_sec'] = self.sb_looming_expansion_time_sec.value()
        state['looming_expansion_speed_mm_per_sec'] = self.sb_looming_expansion_speed_mm_per_sec.value()
        state['looming_expansion_speed_deg_per_sec'] = self.sb_looming_expansion_speed_deg_per_sec.value()
        state['looming_angle_start_deg'] = self.sb_looming_angle_start_deg.value()
        state['looming_angle_stop_deg'] = self.sb_looming_angle_stop_deg.value()
        state['looming_size_to_speed_ratio_ms'] = self.sb_looming_size_to_speed_ratio.value()
        return state
    
    def set_state(self, state: Dict) -> None:
        
        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'looming_type',
            setter = self.cb_looming_type.setCurrentIndex,
            default = self.looming_type
        )
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
        set_from_dict(
            dictionary = state,
            key = 'looming_expansion_speed_deg_per_sec',
            setter = self.sb_looming_expansion_speed_deg_per_sec.setValue,
            default = self.looming_expansion_speed_deg_per_sec,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'looming_angle_start_deg',
            setter = self.sb_looming_angle_start_deg.setValue,
            default = self.looming_angle_start_deg,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'looming_angle_stop_deg',
            setter = self.sb_looming_angle_stop_deg.setValue,
            default = self.looming_angle_stop_deg,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'looming_size_to_speed_ratio_ms',
            setter = self.sb_looming_size_to_speed_ratio.setValue,
            default = self.looming_size_to_speed_ratio_ms,
            cast = float
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:

        super().from_protocol_item(protocol_item)

        if isinstance(protocol_item, Looming):
            self.cb_looming_type.setCurrentIndex(protocol_item.looming_type)
            self.sb_looming_center_mm_x.setValue(protocol_item.looming_center_mm[0])
            self.sb_looming_center_mm_y.setValue(protocol_item.looming_center_mm[1])
            self.sb_looming_period_sec.setValue(protocol_item.looming_period_sec)
            self.sb_looming_expansion_time_sec.setValue(protocol_item.looming_expansion_time_sec)
            self.sb_looming_expansion_speed_mm_per_sec.setValue(protocol_item.looming_expansion_speed_mm_per_sec)
            self.sb_looming_expansion_speed_deg_per_sec.setValue(protocol_item.looming_expansion_speed_deg_per_sec)
            self.sb_looming_angle_start_deg.setValue(protocol_item.looming_angle_start_deg)
            self.sb_looming_angle_stop_deg.setValue(protocol_item.looming_angle_stop_deg)
            self.sb_looming_size_to_speed_ratio.setValue(protocol_item.looming_size_to_speed_ratio_ms)

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
        closed_loop = self.chb_closed_loop.isChecked()

        protocol = Looming(
            foreground_color = foreground_color,
            background_color = background_color,
            closed_loop = closed_loop,
            looming_type = LoomingType(self.cb_looming_type.currentIndex()),
            looming_center_mm = (
                self.sb_looming_center_mm_x.value(),
                self.sb_looming_center_mm_y.value()
            ),
            looming_period_sec = self.sb_looming_period_sec.value(),
            looming_expansion_time_sec = self.sb_looming_expansion_time_sec.value(),
            looming_expansion_speed_mm_per_sec = self.sb_looming_expansion_speed_mm_per_sec.value(),
            looming_expansion_speed_deg_per_sec = self.sb_looming_expansion_speed_deg_per_sec.value(),
            looming_angle_start_deg = self.sb_looming_angle_start_deg.value(),
            looming_angle_stop_deg = self.sb_looming_angle_stop_deg.value(),
            looming_size_to_speed_ratio_ms = self.sb_looming_size_to_speed_ratio.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )
        return protocol

    
if __name__ == '__main__':

    app = QApplication([])
    window1 = LoomingWidget(
        looming_center_mm = (0,0),
        looming_period_sec = 10,
        looming_expansion_time_sec = 10,
        looming_expansion_speed_deg_per_sec = 10,
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window1.show()
    app.exec()
 

