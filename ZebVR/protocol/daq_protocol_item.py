
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
            *args,
            **kwargs
        ) -> None:

        self.daq_boards = daq_boards
        self.board_types = list(daq_boards.keys())

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        # Combobox with board type
        self.daq_combobox = LabeledComboBox()
        self.daq_combobox.setText('DAQ Board')
        for board_type in self.board_types:
            self.daq_combobox.addItem(str(board_type))
        self.daq_combobox.currentIndexChanged.connect(self.on_board_change)

    def on_board_change(self):
        self.state_changed.emit()

    def layout_components(self) -> None:

        super().layout_components()
        self.main_layout.addWidget(self.daq_combobox)

    def get_state(self) -> Dict:

        state = super().get_state()
        state['board_type'] = self.board_types[self.daq_combobox.currentIndex()]
        return state

    def set_state(self, state: Dict) -> None:

        super().set_state(state)
        
        # not sure how to do that properly or if that even makes sense?
        set_from_dict(
            dictionary = state,
            key = 'board_type',
            setter = self.daq_combobox.setCurrentIndex,
            default = self.amplitude_dB,
            cast = float
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:
        self.daq_combobox.setValue(protocol_item.board_type)

    def to_protocol_item(self) -> ProtocolItem:
        ...
