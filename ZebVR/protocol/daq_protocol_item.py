
from typing import Tuple, Dict, Union, List
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QListWidget,
)
from functools import partial
from qt_widgets import LabeledComboBox
from .default import DEFAULT
from .protocol_item import ProtocolItem, DAQ_ProtocolItem, ProtocolItemWidget
from ..utils import set_from_dict
from daq_tools import (
    BoardInfo,
    BoardType
)

def select_items_by_text(list_widget: QListWidget, texts: List[str]):
    for i in range(list_widget.count()):
        item = list_widget.item(i)
        if item.text() in texts:
            item.setSelected(True)  
        else:
            item.setSelected(False)      

class DAQ_ProtocolItemWidget(ProtocolItemWidget):
    
    state_changed = pyqtSignal()

    def __init__(
            self,
            boards: Dict[BoardType, List[BoardInfo]],
            board_type: BoardType = DEFAULT['daq_board_type'],
            board_id: Union[str, int] = DEFAULT['daq_board_id'],
            channels: List = DEFAULT['daq_channels'],
            *args,
            **kwargs
        ) -> None:

        self.boards = boards
        self.board_types = list(boards.keys())
        self.board_type = board_type
        self.board_id = board_id
        self.channels = channels

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        # Combobox with board type
        self.board_type_cb = LabeledComboBox()
        self.board_type_cb.setText('DAQ Board Type')
        for bt in self.board_types:
            self.board_type_cb.addItem(str(bt))
        self.board_type_cb.currentIndexChanged.connect(self.on_board_type_change)
        self.current_board_type = self.board_types[self.board_type_cb.currentIndex()]
        
        # board ID
        self.board_id_cb = LabeledComboBox()
        self.board_id_cb.setText('DAQ Board ID')
        for board in self.boards[self.current_board_type]:
            self.board_id_cb.addItem(str(board.id))
        self.board_id_cb.currentIndexChanged.connect(self.on_board_id_change)
        self.current_board = self.boards[self.current_board_type][self.board_id_cb.currentIndex()]

        # channels
        self.channel_list = QListWidget()
        self.channel_list.setSelectionMode(QListWidget.MultiSelection)

    def on_board_type_change(self):

        self.current_board_type = self.board_types[self.board_type_cb.currentIndex()]
        self.board_id_cb.clear()
        for board in self.boards[self.current_board_type]:
            self.board_id_cb.addItem(str(board.id))

        self.state_changed.emit()

    def on_board_id_change(self):

        # add logic in daughter class / emit signal
        self.current_board = self.boards[self.current_board_type][self.board_id_cb.currentIndex()]
      
    def layout_components(self) -> None:

        super().layout_components()
        self.main_layout.addWidget(self.board_type_cb)
        self.main_layout.addWidget(self.board_id_cb)
        self.main_layout.addWidget(self.channel_list)

    def get_state(self) -> Dict:

        channel_list_widget = self.channel_list.selectedItems()
        channels = [int(widget.text()) for widget in channel_list_widget]

        state = super().get_state()
        state['board_type'] = self.current_board_type
        state['board_id'] = self.current_board.id
        state['channels'] = channels
        return state

    def set_state(self, state: Dict) -> None:

        super().set_state(state)
        
        set_from_dict(
            dictionary = state,
            key = 'board_type',
            setter = self.board_type_cb.setCurrentText,
            default = self.board_type,
            cast = str
        )
        set_from_dict(
            dictionary = state,
            key = 'board_id',
            setter = self.board_id_cb.setCurrentText,
            default = self.board_id,
            cast = str
        )
        set_from_dict(
            dictionary = state,
            key = 'channels',
            setter = partial(select_items_by_text, self.channel_list),
            default = self.channels,
            cast = lambda x: list(map(str, x))
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:
        
        if isinstance(protocol_item, DAQ_ProtocolItem):
            self.board_type_cb.setCurrentText(str(protocol_item.board_type))
            self.board_id_cb.setCurrentText(str(protocol_item.board_id))
            select_items_by_text(self.channel_list, [str(c) for c in protocol_item.channels])

    def to_protocol_item(self) -> DAQ_ProtocolItem:
        ...

