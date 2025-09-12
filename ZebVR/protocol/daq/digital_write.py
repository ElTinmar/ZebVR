from daq_tools import BoardType, BoardInfo
from ZebVR.protocol import (
    Stim, 
    ProtocolItem,
    DAQ_ProtocolItem,
    DAQ_ProtocolItemWidget, 
    StopWidget, 
    Debouncer
)
from typing import Dict, List
from PyQt5.QtWidgets import (
    QApplication, 
    QCheckBox,
)
from qt_widgets import LabeledDoubleSpinBox
from ..default import DEFAULT
from ...utils import set_from_dict

class DigitalWrite(DAQ_ProtocolItem):

    STIM_SELECT = Stim.DIGITAL_WRITE

    def __init__(
        self, 
        digital_level: bool = DEFAULT['daq_digital_level'],
        *args,
        **kwargs
    ) -> None:
        
        super().__init__(*args, **kwargs)
        self.digital_level = digital_level
    
    def start(self) -> Dict:

        super().start() 
        
        command = {
            'stim_select': self.STIM_SELECT,
            'board_type': self.board_type,
            'board_id': self.board_id,
            'channels': self.channels,
            'digital_level': self.digital_level,
        }
        return command
    
class DigitalWriteWidget(DAQ_ProtocolItemWidget):

    def __init__(
            self, 
            digital_level: bool = DEFAULT['daq_digital_level'],
            *args, 
            **kwargs
        ) -> None:

        self.digital_level = digital_level

        super().__init__(*args, **kwargs)

    def set_boards(self, boards: Dict[BoardType, List[BoardInfo]]) -> None:
        
        super().set_boards(boards)
        
        if not boards:
           return

        for channel in self.current_board.digital_output:
            self.channel_list.addItem(str(channel))

    def declare_components(self) -> None:
        
        super().declare_components()

        self.chckb_level = QCheckBox('ON / OFF')
        self.chckb_level.setChecked(False)
        self.chckb_level.stateChanged.connect(self.state_changed)  

    def layout_components(self) -> None:
        
        super().layout_components()
        self.main_layout.addWidget(self.chckb_level)
        self.main_layout.addWidget(self.stop_widget)

    def on_board_id_change(self):
        # change available channels
        
        super().on_board_id_change()
        self.channel_list.clear()
        for channel in self.current_board.digital_output:
            self.channel_list.addItem(str(channel))

        self.state_changed.emit()

    def get_state(self) -> Dict:
        state = super().get_state()
        state['digital_level'] = self.chckb_level.isChecked()
        return state
    
    def set_state(self, state: Dict) -> None:

        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'digital_level',
            setter = self.chckb_level.setChecked,
            default = self.digital_level,
            cast = bool
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:

        super().from_protocol_item(protocol_item)
        if isinstance(protocol_item, DigitalWrite):
            self.chckb_level.setChecked(protocol_item.digital_level)

    def to_protocol_item(self) -> DigitalWrite:

        channel_list_widget = self.channel_list.selectedItems()
        channels = [int(widget.text()) for widget in channel_list_widget]
    
        return DigitalWrite(
            board_type = self.current_board_type,
            board_id = self.current_board.id,
            channels = channels,
            digital_level = self.chckb_level.isChecked(),
            stop_condition = self.stop_widget.to_stop_condition()
        )

if __name__ == '__main__':

    from daq_tools import Arduino_SoftTiming, LabJackU3_SoftTiming, NI_SoftTiming
    
    boards = {
        BoardType.ARDUINO: Arduino_SoftTiming.list_boards(), 
        BoardType.LABJACK: LabJackU3_SoftTiming.list_boards(), 
        BoardType.NATIONAL_INSTRUMENTS: NI_SoftTiming.list_boards()
    }

    app = QApplication([])
    window = DigitalWriteWidget(
        boards = boards,
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
    
    digital_write = window.to_protocol_item()
    print(digital_write.start())