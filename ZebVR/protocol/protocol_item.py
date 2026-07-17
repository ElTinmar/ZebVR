from typing import Optional, Dict, Any, Tuple, Union, List, Type
from abc import ABC
from .stop_condition import StopCondition, Pause, StopWidget
from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
    QWidget, 
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStyle,
    QSizePolicy,
    QMenu,
    QTabWidget, 
    QTabBar
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


class CompositeProtocolItem(ProtocolItem):

    def __init__(
        self,
        sub_protocols: List[ProtocolItem],
        *args,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.sub_protocols = sub_protocols
        self._sync_stop_conditions()

    def _sync_stop_conditions(self):
        for sub in self.sub_protocols:
            sub.set_stop_condition(self.stop_condition)

    def set_stop_condition(self, stop_condition: StopCondition):
        super().set_stop_condition(stop_condition)
        self._sync_stop_conditions()

    def start(self) -> Dict:
        command = super().start()
        sub_commands = [sub.start() for sub in self.sub_protocols]
        command.update({
            'composite': True,
            'sub_commands': sub_commands
        })
        return command

    def initialize(self):
        for sub in self.sub_protocols:
            sub.initialize()

    def cleanup(self):
        for sub in self.sub_protocols:
            sub.cleanup()

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
            fade_in_duration_sec: float = DEFAULT['fade_in_duration_sec'],
            fade_out_duration_sec: float = DEFAULT['fade_out_duration_sec'],
            stimulus_duration_sec: float = DEFAULT['stimulus_duration_sec'],
            coordinate_system: CoordinateSystem = DEFAULT['coordinate_system'], 
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.foreground_color = foreground_color
        self.background_color = background_color
        self.fade_in_duration_sec = fade_in_duration_sec
        self.fade_out_duration_sec = fade_out_duration_sec
        self.stimulus_duration_sec = stimulus_duration_sec
        self.coordinate_system = coordinate_system

    def start(self) -> Dict:
        command = super().start()
        command.update({
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'fade_in_duration_sec': self.fade_in_duration_sec,
            'fade_out_duration_sec': self.fade_out_duration_sec,
            'stimulus_duration_sec': self.stimulus_duration_sec,
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

    def _get_protocol_kwargs(self) -> Dict[str, Any]:
        return {
            'name': self.stim_name.text(),
            'stop_condition': self.stop_widget.to_stop_condition()
        }

    def to_protocol_item(self) -> ProtocolItem:
        return ProtocolItem(**self._get_protocol_kwargs())
    

class CompositeProtocolItemWidget(ProtocolItemWidget):
    
    item_added = Signal(QWidget) 

    def __init__(self, stop_widget: StopWidget, *args, **kwargs):
        self.sub_widgets: List[ProtocolItemWidget] = []
        self._allowed_types: Dict[str, Type[ProtocolItemWidget]] = {}
        
        super().__init__(stop_widget, *args, **kwargs)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

    def register_allowed_type(self, display_name: str, widget_cls: Type[ProtocolItemWidget]) -> None:
        self._allowed_types[display_name] = widget_cls
        self._update_add_menu()

    def declare_components(self) -> None:
        super().declare_components()
        
        self.tabs = QTabWidget(self)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._on_tab_close_requested)
        
        self.add_button = QPushButton("Add Protocol Item...", self)
        self.add_menu = QMenu(self)
        self.add_button.setMenu(self.add_menu)
        self._update_add_menu()

    def _update_add_menu(self) -> None:
        self.add_menu.clear()
        for name, widget_cls in self._allowed_types.items():
            action = self.add_menu.addAction(name)
            action.triggered.connect(lambda checked=False, cls=widget_cls: self._on_add_item_triggered(cls))

    def layout_components(self) -> None:
        self.main_layout = QVBoxLayout(self)
        
        # Layout top settings, then our button and our structural sub-tabs
        self.main_layout.addWidget(self.stim_name)
        self.main_layout.addWidget(self.add_button)
        self.main_layout.addWidget(self.tabs)
        self.main_layout.addWidget(self.stop_widget)

    def add_sub_widget(self, widget: ProtocolItemWidget, display_name: str = "Item") -> None:
        self.sub_widgets.append(widget)
        widget.stop_widget.hide()  

        tab_title = f"{len(self.sub_widgets)}: {display_name}"
        new_index = self.tabs.addTab(widget, tab_title)
        self.tabs.setCurrentIndex(new_index)          
        widget.state_changed.connect(self.state_changed)
        self.state_changed.emit()

    def _on_tab_close_requested(self, index: int) -> None:
        widget = self.tabs.widget(index)
        if widget in self.sub_widgets:
            self.sub_widgets.remove(widget)
            
        self.tabs.removeTab(index)
        widget.setParent(None)
        widget.deleteLater()
        
        self._refresh_tab_titles()
        self.state_changed.emit()

    def _refresh_tab_titles(self) -> None:
        for i in range(self.tabs.count()):
            current_title = self.tabs.tabText(i)
            if ":" in current_title:
                suffix = current_title.split(":", 1)[1]
                self.tabs.setTabText(i, f"{i + 1}:{suffix}")

    def _on_add_item_triggered(self, widget_cls: Type[ProtocolItemWidget]) -> None:
        new_stop_widget = StopWidget(
            debouncer=self.stop_widget.debouncer,
            background_image=self.stop_widget.background_image
        )
        
        # Watch out for DAQ_ProtocolItemWidget, pass a partial from stim widget?
        new_widget = widget_cls(stop_widget=new_stop_widget)

        # Lookup friendly display string name from our registry map configuration
        display_name = [k for k, v in self._allowed_types.items() if v == widget_cls][0]
        
        self.add_sub_widget(new_widget, display_name)
        self.item_added.emit(new_widget)

    def to_protocol_item(self) -> CompositeProtocolItem:
        sub_protocols = [widget.to_protocol_item() for widget in self.sub_widgets]
        return CompositeProtocolItem(
            sub_protocols=sub_protocols,
            **self._get_protocol_kwargs()
        )