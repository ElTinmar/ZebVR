from typing import Optional, Tuple, Dict, Any
from abc import ABC
from enum import IntEnum
from .stop_condition import StopCondition, Pause, StopWidget
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, 
    QLabel,
    QHBoxLayout,
    QVBoxLayout
)
from qt_widgets import LabeledDoubleSpinBox
from ..utils import set_from_dict

class Stim:
    class Visual(IntEnum):
        DARK = 0
        BRIGHT = 1
        PHOTOTAXIS = 2
        OMR = 3
        OKR = 4
        FOLLOWING_LOOMING = 5
        PREY_CAPTURE = 6
        LOOMING = 7
        CONCENTRIC_GRATING = 8
        FOLLOWING_DOT = 9
        DOT = 10
        IMAGE = 11
        BRIGHTNESS_RAMP = 12

        def __str__(self):
            return self.name
    
    class Acoustic(IntEnum):
        PURE_TONE = 0
        WHITE_NOISE = 1
        PINK_NOISE = 2

        def __str__(self):
            return self.name
        
class ProtocolItem(ABC):

    STIM_SELECT: Optional[int] = None

    def __init__(self, stop_condition: StopCondition = Pause()):
        self.stop_condition = stop_condition

    def start(self) -> Optional[Dict]:
        self.stop_condition.start()

    def done(self, metadata: Optional[Any]) -> bool:
        return self.stop_condition.done(metadata)

    def initialize(self):
        '''Run init steps in target worker process'''
        pass

    def cleanup(self):
        '''Run cleanup steps in target worker process'''
        pass

    def set_stop_condition(self, stop_condition: StopCondition):
        self.stop_condition = stop_condition

class ProtocolItemWidget(QWidget):
    
    state_changed = pyqtSignal()

    def __init__(self, stop_widget: StopWidget, *args, **kwargs) -> None:
        
        super().__init__(*args, **kwargs)

        self.stop_widget = stop_widget
        self.declare_components()
        self.layout_components() 

    def declare_components(self) -> None:
        ...

    def layout_components(self) -> None:
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:
        ...

    def set_state(self, state: Dict) -> None:
        ...

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:
        ...

    def to_protocol_item(self) -> ProtocolItem:
        ...

class VisualProtocolItemWidget(ProtocolItemWidget):
    
    state_changed = pyqtSignal()

    def __init__(
            self,
            foreground_color: Tuple = (0.2, 0.2, 0.2, 1.0),
            background_color: Tuple = (0.0, 0.0, 0.0, 1.0),
            *args,
            **kwargs
        ) -> None:

        
        self.foreground_color = foreground_color
        self.background_color = background_color

        super().__init__(*args, **kwargs)

        
    def declare_components(self) -> None:

        super().declare_components()

        self.lbl_foreground_color = QLabel('Foreground color:')

        self.sb_foreground_color_R = LabeledDoubleSpinBox()
        self.sb_foreground_color_R.setText('R')
        self.sb_foreground_color_R.setRange(0,1)
        self.sb_foreground_color_R.setSingleStep(0.05)
        self.sb_foreground_color_R.setValue(self.foreground_color[0])
        self.sb_foreground_color_R.valueChanged.connect(self.state_changed)

        self.sb_foreground_color_G = LabeledDoubleSpinBox()
        self.sb_foreground_color_G.setText('G')
        self.sb_foreground_color_G.setRange(0,1)
        self.sb_foreground_color_G.setSingleStep(0.05)
        self.sb_foreground_color_G.setValue(self.foreground_color[1])
        self.sb_foreground_color_G.valueChanged.connect(self.state_changed)

        self.sb_foreground_color_B = LabeledDoubleSpinBox()
        self.sb_foreground_color_B.setText('B')
        self.sb_foreground_color_B.setRange(0,1)
        self.sb_foreground_color_B.setSingleStep(0.05)
        self.sb_foreground_color_B.setValue(self.foreground_color[2])
        self.sb_foreground_color_B.valueChanged.connect(self.state_changed)

        self.sb_foreground_color_A = LabeledDoubleSpinBox()
        self.sb_foreground_color_A.setText('A')
        self.sb_foreground_color_A.setRange(0,1)
        self.sb_foreground_color_A.setSingleStep(0.05)
        self.sb_foreground_color_A.setValue(self.foreground_color[3])
        self.sb_foreground_color_A.valueChanged.connect(self.state_changed)

        self.lbl_background_color = QLabel('Background color:')

        self.sb_background_color_R = LabeledDoubleSpinBox()
        self.sb_background_color_R.setText('R')
        self.sb_background_color_R.setRange(0,1)
        self.sb_background_color_R.setSingleStep(0.05)
        self.sb_background_color_R.setValue(self.background_color[0])
        self.sb_background_color_R.valueChanged.connect(self.state_changed)

        self.sb_background_color_G = LabeledDoubleSpinBox()
        self.sb_background_color_G.setText('G')
        self.sb_background_color_G.setRange(0,1)
        self.sb_background_color_G.setSingleStep(0.05)
        self.sb_background_color_G.setValue(self.background_color[1])
        self.sb_background_color_G.valueChanged.connect(self.state_changed)

        self.sb_background_color_B = LabeledDoubleSpinBox()
        self.sb_background_color_B.setText('B')
        self.sb_background_color_B.setRange(0,1)
        self.sb_background_color_B.setSingleStep(0.05)
        self.sb_background_color_B.setValue(self.background_color[2])
        self.sb_background_color_B.valueChanged.connect(self.state_changed)

        self.sb_background_color_A = LabeledDoubleSpinBox()
        self.sb_background_color_A.setText('A')
        self.sb_background_color_A.setRange(0,1)
        self.sb_background_color_A.setSingleStep(0.05)
        self.sb_background_color_A.setValue(self.background_color[3])
        self.sb_background_color_A.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:

        super().layout_components()

        foreground_color_layout = QHBoxLayout()
        foreground_color_layout.addWidget(self.lbl_foreground_color)
        foreground_color_layout.addWidget(self.sb_foreground_color_R)
        foreground_color_layout.addWidget(self.sb_foreground_color_G)
        foreground_color_layout.addWidget(self.sb_foreground_color_B)
        foreground_color_layout.addWidget(self.sb_foreground_color_A)
        foreground_color_layout.addStretch()

        background_color_layout = QHBoxLayout()
        background_color_layout.addWidget(self.lbl_background_color)
        background_color_layout.addWidget(self.sb_background_color_R)
        background_color_layout.addWidget(self.sb_background_color_G)
        background_color_layout.addWidget(self.sb_background_color_B)
        background_color_layout.addWidget(self.sb_background_color_A)
        background_color_layout.addStretch()

        self.main_layout.addLayout(foreground_color_layout)
        self.main_layout.addLayout(background_color_layout)

    def get_state(self) -> Dict:

        state = {} 
        state['foreground_color'] = (
            self.sb_foreground_color_R.value(),
            self.sb_foreground_color_G.value(),
            self.sb_foreground_color_B.value(),
            self.sb_foreground_color_A.value()
        )
        state['background_color'] = (
            self.sb_background_color_R.value(),
            self.sb_background_color_G.value(),
            self.sb_background_color_B.value(),
            self.sb_background_color_A.value()
        )
        return state

    def set_state(self, state: Dict) -> None:

        set_from_dict(
            dictionary = state,
            key = 'foreground_color',
            setter = self.sb_foreground_color_R.setValue,
            default = self.foreground_color,
            cast = lambda x: float(x[0])
        )
        set_from_dict(
            dictionary = state,
            key = 'foreground_color',
            setter = self.sb_foreground_color_G.setValue,
            default = self.foreground_color,
            cast = lambda x: float(x[1])
        )
        set_from_dict(
            dictionary = state,
            key = 'foreground_color',
            setter = self.sb_foreground_color_B.setValue,
            default = self.foreground_color,
            cast = lambda x: float(x[2])
        )
        set_from_dict(
            dictionary = state,
            key = 'foreground_color',
            setter = self.sb_foreground_color_A.setValue,
            default = self.foreground_color,
            cast = lambda x: float(x[3])
        )

        set_from_dict(
            dictionary = state,
            key = 'background_color',
            setter = self.sb_background_color_R.setValue,
            default = self.background_color,
            cast = lambda x: float(x[0])
        )
        set_from_dict(
            dictionary = state,
            key = 'background_color',
            setter = self.sb_background_color_G.setValue,
            default = self.background_color,
            cast = lambda x: float(x[1])
        )
        set_from_dict(
            dictionary = state,
            key = 'background_color',
            setter = self.sb_background_color_B.setValue,
            default = self.background_color,
            cast = lambda x: float(x[2])
        )
        set_from_dict(
            dictionary = state,
            key = 'background_color',
            setter = self.sb_background_color_A.setValue,
            default = self.background_color,
            cast = lambda x: float(x[3])
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:
        
        self.sb_foreground_color_R.setValue(protocol_item.foreground_color[0])
        self.sb_foreground_color_G.setValue(protocol_item.foreground_color[1])
        self.sb_foreground_color_B.setValue(protocol_item.foreground_color[2])
        self.sb_foreground_color_A.setValue(protocol_item.foreground_color[3])
        
        self.sb_background_color_R.setValue(protocol_item.background_color[0])
        self.sb_background_color_G.setValue(protocol_item.background_color[1])
        self.sb_background_color_B.setValue(protocol_item.background_color[2])
        self.sb_background_color_A.setValue(protocol_item.background_color[3])  

    def to_protocol_item(self) -> ProtocolItem:
        ...

class Image(ProtocolItem):

    STIM_SELECT = Stim.Visual.IMAGE

    def __init__(
            self, 
            image_path: str,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.image_path = image_path
        self.foreground_color = foreground_color
        self.background_color = background_color 

    def start(self) -> Dict:

        super().start()

        command = {
            'stim_select': self.STIM_SELECT,
            'image_path': str(self.image_path),
            'foreground_color': self.foreground_color,
            'background_color': self.background_color
        }
        return command
    

class Phototaxis(ProtocolItem):

    STIM_SELECT = Stim.Visual.PHOTOTAXIS

    def __init__(
            self, 
            phototaxis_polarity: int,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.phototaxis_polarity = phototaxis_polarity
        self.foreground_color = foreground_color
        self.background_color = background_color 

    def start(self) -> Dict:

        super().start()

        command = {
            'stim_select': self.STIM_SELECT,
            'phototaxis_polarity': self.phototaxis_polarity,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color
        }
        return command
    
class OKR(ProtocolItem):

    STIM_SELECT = Stim.Visual.OKR

    def __init__(
            self, 
            okr_spatial_frequency_deg: float,
            okr_speed_deg_per_sec: float,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
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

class ConcentricGrating(ProtocolItem):

    STIM_SELECT = Stim.Visual.CONCENTRIC_GRATING

    def __init__(
            self, 
            spatial_period_mm: float,
            speed_mm_per_sec: float,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.spatial_period_mm = spatial_period_mm
        self.speed_mm_per_sec = speed_mm_per_sec
        self.foreground_color = foreground_color
        self.background_color = background_color 

    def start(self) -> Dict:

        super().start()

        command = {
            'stim_select': self.STIM_SELECT,
            'concentric_spatial_period_mm': self.spatial_period_mm,
            'concentric_speed_mm_per_sec': self.speed_mm_per_sec,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color
        }
        return command
    
class OMR(ProtocolItem):
    
    STIM_SELECT = Stim.Visual.OMR
    
    def __init__(
            self, 
            omr_spatial_period_mm: float,
            omr_angle_deg: float,
            omr_speed_mm_per_sec: float,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.omr_spatial_period_mm = omr_spatial_period_mm
        self.omr_angle_deg = omr_angle_deg
        self.omr_speed_mm_per_sec = omr_speed_mm_per_sec
        self.foreground_color = foreground_color
        self.background_color = background_color 
    
    def start(self) -> Dict:

        super().start()

        command = {
            'stim_select': self.STIM_SELECT,
            'omr_spatial_period_mm': self.omr_spatial_period_mm,
            'omr_angle_deg': self.omr_angle_deg,
            'omr_speed_mm_per_sec': self.omr_speed_mm_per_sec,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color
        }
        return command

class Dark(ProtocolItem):

    STIM_SELECT = Stim.Visual.DARK

    def __init__(
            self,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.foreground_color = foreground_color
        self.background_color = background_color 

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color
        }
        return command

class Bright(ProtocolItem):

    STIM_SELECT = Stim.Visual.BRIGHT

    def __init__(
            self, 
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.foreground_color = foreground_color 
        self.background_color = background_color 

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color
        }
        return command

class FollowingLooming(ProtocolItem):

    STIM_SELECT = Stim.Visual.FOLLOWING_LOOMING

    def __init__(
            self, 
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            looming_center_mm: Tuple[float, float],
            looming_period_sec: float,
            looming_expansion_time_sec: float,
            looming_expansion_speed_mm_per_sec: float,
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
            'following_looming_center_mm': self.looming_center_mm,
            'following_looming_period_sec': self.looming_period_sec,
            'following_looming_expansion_time_sec': self.looming_expansion_time_sec,
            'following_looming_expansion_speed_mm_per_sec': self.looming_expansion_speed_mm_per_sec,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color
        }
        return command 

class FollowingDot(ProtocolItem):

    STIM_SELECT = Stim.Visual.FOLLOWING_DOT

    def __init__(
            self, 
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            dot_center_mm: Tuple[float, float],
            dot_radius_mm: float,
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
    
class Looming(ProtocolItem):

    STIM_SELECT = Stim.Visual.LOOMING

    def __init__(
            self, 
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            looming_center_mm: Tuple[float, float],
            looming_period_sec: float,
            looming_expansion_time_sec: float,
            looming_expansion_speed_mm_per_sec: float,
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

class PreyCapture(ProtocolItem):

    STIM_SELECT = Stim.Visual.PREY_CAPTURE

    def __init__(
            self, 
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            n_preys: int = 50,
            prey_speed_mm_s: float = 0.75,
            prey_radius_mm: float = 0.25,
            *args,
            **kwargs   
        ) -> None:

        super().__init__(*args, **kwargs)
        self.foreground_color = foreground_color 
        self.background_color = background_color
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
    
class PureTone(ProtocolItem):
    pass

class WhiteNoise(ProtocolItem):
    pass

class PinkNoise(ProtocolItem):
    pass
