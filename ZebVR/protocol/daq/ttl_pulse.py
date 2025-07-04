from daq_tools import BoardInfo, BoardType
from ZebVR.protocol import (
    Stim, 
    ProtocolItem, 
    DAQ_ProtocolItem,
    DAQ_ProtocolItemWidget, 
    StopWidget, 
    Debouncer
)
from typing import List, Dict, Union
from PyQt5.QtWidgets import (
    QApplication, 
    QListWidget
)
from qt_widgets import LabeledDoubleSpinBox
from ...utils import set_from_dict
from ..default import DEFAULT

class TTL_Pulse(DAQ_ProtocolItem):

    STIM_SELECT = Stim.TTL_PULSE

    def __init__(
        self, 
        daq_DO_channels: List[int] = DEFAULT['daq_DO_channel'],
        daq_ttl_duration_msec: float = DEFAULT['daq_ttl_duration_msec'],
        *args,
        **kwargs
    ) -> None:
        
        super().__init__(*args, **kwargs)

        self.daq_DO_channels = daq_DO_channels
        self.daq_ttl_duration_msec = daq_ttl_duration_msec
    
    def start(self) -> Dict:

        super().start() 
        
        command = {
            'stim_select': self.STIM_SELECT,
            'daq_board_type': self.daq_board_type,
            'daq_board_id': self.daq_board_id,
            'daq_DO_channels': self.daq_DO_channels,
            'daq_ttl_duration_msec': self.daq_ttl_duration_msec,
        }
        return command
    
class TTL_PulseWidget(DAQ_ProtocolItemWidget):

    def __init__(
            self, 
            daq_DO_channels: List[int] = DEFAULT['daq_DO_channel'],
            daq_ttl_duration_msec: float = DEFAULT['daq_ttl_duration_msec'],
            *args, 
            **kwargs
        ) -> None:

        self.daq_DO_channels = daq_DO_channels
        self.daq_ttl_duration_msec = daq_ttl_duration_msec
        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:
        
        super().declare_components()

        self.do_channel_list = QListWidget()
        self.do_channel_list.setSelectionMode(QListWidget.MultiSelection)
        for channel in self.current_board.digital_output:
            self.do_channel_list.addItem(str(channel))

        self.sb_ttl_pulse_duration_msec = LabeledDoubleSpinBox()
        self.sb_ttl_pulse_duration_msec.setText('Pulse duration (msec)')
        self.sb_ttl_pulse_duration_msec.setRange(1, 1_000.0)
        self.sb_ttl_pulse_duration_msec.setValue(self.daq_ttl_duration_msec)
        self.sb_ttl_pulse_duration_msec.valueChanged.connect(self.state_changed)       
        
    def on_board_id_change(self):
        # change available channels
        
        super().on_board_id_change()
        self.do_channel_list.clear()
        for channel in self.current_board.digital_output:
            self.do_channel_list.addItem(str(channel))

        self.state_changed.emit()

    def layout_components(self) -> None:
        
        super().layout_components()
        self.main_layout.addWidget(self.do_channel_list)
        self.main_layout.addWidget(self.sb_ttl_pulse_duration_msec)
        self.main_layout.addWidget(self.stop_widget)

    def to_protocol_item(self) -> TTL_Pulse:

        channel_list_widget = self.do_channel_list.selectedItems()
        channels = [int(widget.text()) for widget in channel_list_widget]
    
        return TTL_Pulse(
            daq_board_type = self.current_board_type,
            daq_board_id = self.current_board.id,
            daq_DO_channels = channels,
            daq_ttl_duration_msec = self.sb_ttl_pulse_duration_msec.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )

if __name__ == '__main__':

    from daq_tools import Arduino_SoftTiming, LabJackU3_SoftTiming, NI_SoftTiming
    
    daq_boards = {
        BoardType.ARDUINO: Arduino_SoftTiming.list_boards(), 
        BoardType.LABJACK: LabJackU3_SoftTiming.list_boards(), 
        BoardType.NATIONAL_INSTRUMENTS: NI_SoftTiming.list_boards()
    }

    app = QApplication([])
    window = TTL_PulseWidget(
        daq_boards = daq_boards,
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
    
    ttl_pulse = window.to_protocol_item()
    print(ttl_pulse.start())