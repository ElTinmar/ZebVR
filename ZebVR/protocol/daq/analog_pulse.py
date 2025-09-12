from daq_tools import BoardInfo, BoardType
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

class AnalogPulse(DAQ_ProtocolItem):

    STIM_SELECT = Stim.ANALOG_PULSE

    def __init__(
        self, 
        pulse_duration_msec: float = DEFAULT['daq_pulse_duration_msec'],
        analog_value: float = DEFAULT['daq_analog_value'],
        *args,
        **kwargs
    ) -> None:
        
        super().__init__(*args, **kwargs)
        self.pulse_duration_msec = pulse_duration_msec
        self.analog_value = analog_value
    
    def start(self) -> Dict:

        super().start() 
        
        command = {
            'stim_select': self.STIM_SELECT,
            'board_type': self.board_type,
            'board_id': self.board_id,
            'channels': self.channels,
            'pulse_duration_msec': self.pulse_duration_msec,
            'analog_value': self.analog_value,
        }
        return command
    
class AnalogPulseWidget(DAQ_ProtocolItemWidget):

    def __init__(
            self, 
            pulse_duration_msec: float = DEFAULT['daq_pulse_duration_msec'],
            analog_value: float = DEFAULT['daq_analog_value'],
            *args, 
            **kwargs
        ) -> None:

        self.pulse_duration_msec = pulse_duration_msec
        self.analog_value = analog_value

        super().__init__(*args, **kwargs)

    def set_boards(self, boards: Dict[BoardType, List[BoardInfo]]) -> None:

        if not boards:
           return

        super().set_boards(boards)

        for channel in self.current_board.analog_output:
            self.channel_list.addItem(str(channel))

    def declare_components(self) -> None:
        
        super().declare_components()

        self.sb_pulse_duration_msec = LabeledDoubleSpinBox()
        self.sb_pulse_duration_msec.setText('Pulse duration (msec)')
        self.sb_pulse_duration_msec.setRange(1, 1_000.0)
        self.sb_pulse_duration_msec.setValue(self.pulse_duration_msec)
        self.sb_pulse_duration_msec.valueChanged.connect(self.state_changed)       
        
        self.sb_analog_value = LabeledDoubleSpinBox()
        self.sb_analog_value.setText('Analog value')
        self.sb_analog_value.setRange(-1000, 1000)
        self.sb_analog_value.setSingleStep(0.1)
        self.sb_analog_value.setValue(self.analog_value)
        self.sb_analog_value.valueChanged.connect(self.state_changed)      

    def layout_components(self) -> None:
        
        super().layout_components()
        self.main_layout.addWidget(self.sb_pulse_duration_msec)
        self.main_layout.addWidget(self.sb_analog_value)
        self.main_layout.addWidget(self.stop_widget)

    def on_board_id_change(self):
        # change available channels
        
        super().on_board_id_change()
        self.channel_list.clear()
        for channel in self.current_board.analog_output:
            self.channel_list.addItem(str(channel))

        self.state_changed.emit()

    def get_state(self) -> Dict:
        state = super().get_state()
        state['pulse_duration_msec'] = self.sb_pulse_duration_msec.value()
        state['analog_value'] = self.sb_analog_value.value()
        return state
    
    def set_state(self, state: Dict) -> None:

        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'pulse_duration_msec',
            setter = self.sb_pulse_duration_msec.setValue,
            default = self.pulse_duration_msec,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'analog_value',
            setter = self.sb_analog_value.setValue,
            default = self.analog_value,
            cast = bool
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:

        super().from_protocol_item(protocol_item)
        if isinstance(protocol_item, AnalogPulse):
            self.sb_pulse_duration_msec.setValue(protocol_item.pulse_duration_msec)
            self.sb_analog_value.setValue(protocol_item.analog_value)

    def to_protocol_item(self) -> AnalogPulse:

        channel_list_widget = self.channel_list.selectedItems()
        channels = [int(widget.text()) for widget in channel_list_widget]
    
        return AnalogPulse(
            board_type = self.current_board_type,
            board_id = self.current_board.id,
            channels = channels,
            pulse_duration_msec = self.sb_pulse_duration_msec.value(),
            analog_value = self.sb_analog_value.value(),
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
    window = AnalogPulseWidget(
        boards = boards,
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
    
    analog_pulse = window.to_protocol_item()
    print(analog_pulse.start())