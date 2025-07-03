from .protocol_item import ProtocolItem, ProtocolItemWidget
from .default import DEFAULT
from typing import Tuple, Dict, Union, List
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QLabel,
    QHBoxLayout,
    QComboBox,
    QApplication
)

from qt_widgets import LabeledDoubleSpinBox
from ..utils import set_from_dict
from daq_tools import (
    Arduino_SoftTiming, 
    LabJackU3_SoftTiming, 
    NI_SoftTiming, 
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

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        # Combobox with board type
        self.daq_combobox = QComboBox()
        for board_type in self.daq_boards.keys():
            self.daq_combobox.addItem(board_type)
        self.daq_combobox.currentItemChanged.connect()

    def layout_components(self) -> None:

        super().layout_components()

        self.main_layout.addWidget(self.sb_amplitude_dB)

    def get_state(self) -> Dict:

        state = super().get_state()
        state['amplitude_dB'] = self.sb_amplitude_dB.value()
        return state

    def set_state(self, state: Dict) -> None:

        super().set_state(state)
        
        set_from_dict(
            dictionary = state,
            key = 'amplitude_dB',
            setter = self.sb_amplitude_dB.setValue,
            default = self.amplitude_dB,
            cast = float
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:
        self.sb_amplitude_dB.setValue(protocol_item.amplitude_dB)

    def to_protocol_item(self) -> ProtocolItem:
        ...

if __name__ == '__main__':

    daq_boards = {
        BoardType.ARDUINO: Arduino_SoftTiming.list_boards(), 
        BoardType.LABJACK: LabJackU3_SoftTiming.list_boards(), 
        BoardType.NATIONAL_INSTRUMENTS: NI_SoftTiming.list_boards()
    }

    app = QApplication([])
    widget = DAQ_ProtocolItemWidget(daq_boards)
    widget.show()
    app.exec_()