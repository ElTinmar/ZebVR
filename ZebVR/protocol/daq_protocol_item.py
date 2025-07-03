
from typing import Tuple, Dict, Union, List
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QLabel,
    QHBoxLayout,
)

from qt_widgets import LabeledComboBox
from .default import DEFAULT
from .protocol_item import ProtocolItem, ProtocolItemWidget
from ..utils import set_from_dict
from daq_tools import (
    BoardInfo,
    BoardType
)

class DAQ_ProtocolItemWidget(ProtocolItemWidget):
    
    state_changed = pyqtSignal()

    def __init__(
            self,
            daq_boards: Dict[BoardType, List[BoardInfo]],
            daq_type: BoardType = DEFAULT['daq_type'],
            daq_board_id: Union[str, int] = DEFAULT['daq_board_id'],
            *args,
            **kwargs
        ) -> None:

        self.daq_boards = daq_boards
        self.board_types = list(daq_boards.keys())
        self.daq_type = daq_type
        self.daq_board_id = daq_board_id

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        # Combobox with board type
        self.daq_type_cb = LabeledComboBox()
        self.daq_type_cb.setText('DAQ Board Type')
        for board_type in self.board_types:
            self.daq_type_cb.addItem(str(board_type))
        self.daq_type_cb.currentIndexChanged.connect(self.on_board_type_change)
        self.current_board_type = self.board_types[self.daq_type_cb.currentIndex()]
        
        # board ID
        self.daq_board_id_cb = LabeledComboBox()
        self.daq_board_id_cb.setText('DAQ Board ID')
        for board in self.daq_boards[self.current_board_type]:
            self.daq_board_id_cb.addItem(str(board.id))
        self.daq_board_id_cb.currentIndexChanged.connect(self.on_daq_board_id_change)
        self.current_board = self.daq_boards[self.current_board_type][self.daq_board_id_cb.currentIndex()]

    def on_board_type_change(self):

        self.current_board_type = self.board_types[self.daq_type_cb.currentIndex()]
        self.daq_board_id_cb.clear()
        for board in self.daq_boards[self.current_board_type]:
            self.daq_board_id_cb.addItem(str(board.id))

        self.state_changed.emit()

    def on_daq_board_id_change(self):

        # add logic in daughter class
        self.current_board = self.daq_boards[self.current_board_type][self.daq_board_id_cb.currentIndex()]
        self.state_changed.emit()

    def layout_components(self) -> None:

        super().layout_components()
        self.main_layout.addWidget(self.daq_type_cb)

    def get_state(self) -> Dict:

        state = super().get_state()
        state['daq_type'] = self.current_board_type
        state['board_id'] = self.current_board.id
        return state

    def set_state(self, state: Dict) -> None:

        super().set_state(state)
        
        set_from_dict(
            dictionary = state,
            key = 'daq_type',
            setter = self.daq_type_cb.setCurrentIndex,
            default = self.daq_type,
        )

        set_from_dict(
            dictionary = state,
            key = 'board_id',
            setter = self.daq_board_id_cb.setCurrentIndex,
            default = self.daq_board_id
        )


    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:
        self.daq_type_cb.setValue(protocol_item.daq_type)

    def to_protocol_item(self) -> ProtocolItem:
        ...
