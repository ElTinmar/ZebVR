from typing import Optional, Dict, Any, Tuple, Union, List
from abc import ABC
from .stop_condition import StopCondition, Pause, StopWidget
from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
    QWidget, 
    QVBoxLayout
)
from qt_widgets import LabeledEditLine
from ..utils import set_from_dict
from daq_tools import BoardType
from .default import DEFAULT
from .stim import CoordinateSystem

class ProtocolItem(ABC):

    STIM_SELECT: Optional[int] = None

    def __init__(
            self, 
            stop_condition: StopCondition = Pause(),
            name: str = DEFAULT['name']
        ):
        self.stop_condition = stop_condition
        self.name = name

    def start(self) -> Dict:
        self.stop_condition.start()
        command = {'name': self.name}
        return command

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

    def start(self) -> Dict:
        command = super().start()
        command.update({
            'board_type': self.board_type,
            'board_id': self.board_id,
            'channels': self.channels,
        })
        return command
    
class AudioProtocolItem(ProtocolItem):

    def __init__(
            self,
            amplitude_dB: float = DEFAULT['amplitude_dB'],
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.amplitude_dB = amplitude_dB

    def start(self) -> Dict:
        command = super().start()
        command.update({'amplitude_dB': self.amplitude_dB})
        return command
    
class VisualProtocolItem(ProtocolItem):
    
    def __init__(
            self,
            foreground_color: Tuple[float,float,float,float] = DEFAULT['foreground_color'],
            background_color: Tuple[float,float,float,float] = DEFAULT['background_color'],
            coordinate_system: CoordinateSystem = DEFAULT['coordinate_system'], 
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.foreground_color = foreground_color
        self.background_color = background_color
        self.coordinate_system = coordinate_system

    def start(self) -> Dict:
        command = super().start()
        command.update({
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'coordinate_system': self.coordinate_system
        })
        return command

class ProtocolItemWidget(QWidget):
    
    state_changed =  Signal()

    def __init__(self, stop_widget: StopWidget, *args, **kwargs) -> None:
        
        super().__init__(*args, **kwargs)

        self.stop_widget = stop_widget
        self.declare_components()
        self.layout_components() 

    def declare_components(self) -> None:
        self.stim_name = LabeledEditLine()
        self.stim_name.setLabel('Name:')
        self.stim_name.setText(DEFAULT['name'])

    def layout_components(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.stim_name)

    def get_state(self) -> Dict:
        state = {}
        state['stop_condition'] = self.stop_widget.get_state()
        state['name'] = self.stim_name.text()
        return state

    def set_state(self, state: Dict) -> None:
        set_from_dict(
            dictionary = state,
            key = 'stop_condition',
            setter = self.stop_widget.set_state,
            default = {}
        )
        set_from_dict(
            dictionary = state,
            key = 'name',
            setter = self.stim_name.setText,
            default = ''
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:
        self.stop_widget.from_stop_condition(protocol_item.stop_condition)
        self.stim_name.setText(protocol_item.name)

    def to_protocol_item(self) -> ProtocolItem:
        ...
