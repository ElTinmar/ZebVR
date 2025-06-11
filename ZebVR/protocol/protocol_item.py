from typing import Optional, Dict, Any
from abc import ABC
from enum import IntEnum
from .stop_condition import StopCondition, Pause, StopWidget
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout
)
from ..utils import set_from_dict

class Stim(IntEnum):

    # visual
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
    RAMP = 12

    # acoustic
    PURE_TONE = 20
    FREQUENCY_RAMP = 21
    WHITE_NOISE = 22
    PINK_NOISE = 23
    CLICK_TRAIN = 24
    SILENCE = 25

    def __str__(self):
        return self.name
    

class RampType(IntEnum):
    LINEAR = 0
    POWER_LAW = 1 # Stevens' law
    LOG = 2 # Fechner's law

    def __str__(self) -> str:
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

    def get_state(self) -> Dict:
        state = {}
        state['stop_condition'] = self.stop_widget.get_state()
        return state

    def set_state(self, state: Dict) -> None:
        set_from_dict(
            dictionary = state,
            key = 'stop_condition',
            setter = self.stop_widget.set_state,
            default = {}
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:
        ...

    def to_protocol_item(self) -> ProtocolItem:
        ...
