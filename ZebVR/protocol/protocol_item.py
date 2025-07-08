from typing import Optional, Dict, Any, Tuple, Union, List
from abc import ABC
from .stop_condition import StopCondition, Pause, StopWidget
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout
)
from ..utils import set_from_dict
from daq_tools import BoardType
from .default import DEFAULT

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


class DAQ_ProtocolItem(ProtocolItem):

    def __init__(
            self,
            board_type: BoardType = DEFAULT['daq_board_type'],
            board_id: Union[str, int] = DEFAULT['daq_board_id'],
            channels: List[int] = DEFAULT['daq_channels'],
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.board_type = board_type
        self.board_id = board_id
        self.channels = channels

class AudioProtocolItem(ProtocolItem):

    def __init__(
            self,
            amplitude_dB: float = DEFAULT['amplitude_dB'],
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.amplitude_dB = amplitude_dB

class VisualProtocolItem(ProtocolItem):
    
    def __init__(
            self,
            foreground_color: Tuple[float,float,float,float] = DEFAULT['foreground_color'],
            background_color: Tuple[float,float,float,float] = DEFAULT['background_color'],
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.foreground_color = foreground_color
        self.background_color = background_color

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
