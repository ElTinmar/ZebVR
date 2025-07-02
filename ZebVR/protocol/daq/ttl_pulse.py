from ZebVR.protocol import Stim, ProtocolItem, DAQ_ProtocolItemWidget, StopWidget, Debouncer
from typing import List, Dict, Union
from PyQt5.QtWidgets import (
    QApplication, 
)
from ...utils import set_from_dict
from ..default import DEFAULT

class TTL_Pulse(ProtocolItem):

    STIM_SELECT = Stim.TTL_PULSE

    def __init__(
        self, 
        daq_board_type: str = DEFAULT['daq_board_type'],
        daq_board_id: Union[int, str] = DEFAULT['daq_board_id'],
        daq_DO_channels: List[int] = DEFAULT['daq_DO_channel'],
        daq_ttl_duration_msec: float = DEFAULT['daq_ttl_duration_msec'],
    ) -> None:

        self.daq_board_type = daq_board_type
        self.daq_board_id = daq_board_id
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

    def layout_components(self) -> None:
        
        super().layout_components()
        self.main_layout.addWidget(self.stop_widget)

    def to_protocol_item(self) -> TTL_Pulse:
        return TTL_Pulse(
            stop_condition = self.stop_widget.to_stop_condition()
        )

if __name__ == '__main__':

    app = QApplication([])
    window = TTL_PulseWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
    