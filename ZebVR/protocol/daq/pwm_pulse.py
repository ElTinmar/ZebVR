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

class PWM_Pulse(DAQ_ProtocolItem):

    STIM_SELECT = Stim.PWM_PULSE

    def __init__(
        self, 
        pulse_duration_msec: float = DEFAULT['daq_pulse_duration_msec'],
        duty_cycle: float = DEFAULT['daq_duty_cycle'],
        *args,
        **kwargs
    ) -> None:
        
        super().__init__(*args, **kwargs)
        self.pulse_duration_msec = pulse_duration_msec
        self.duty_cycle = duty_cycle
    
    def start(self) -> Dict:

        super().start() 
        
        command = {
            'stim_select': self.STIM_SELECT,
            'board_type': self.board_type,
            'board_id': self.board_id,
            'channels': self.channels,
            'pulse_duration_msec': self.pulse_duration_msec,
            'duty_cycle': self.duty_cycle,
        }
        return command
    
class PWM_PulseWidget(DAQ_ProtocolItemWidget):

    def __init__(
            self, 
            pulse_duration_msec: float = DEFAULT['daq_pulse_duration_msec'],
            duty_cycle: float = DEFAULT['daq_duty_cycle'],
            *args, 
            **kwargs
        ) -> None:

        self.pulse_duration_msec = pulse_duration_msec
        self.duty_cycle = duty_cycle

        super().__init__(*args, **kwargs)

    def set_boards(self, boards: Dict[BoardType, List[BoardInfo]]) -> None:

        super().set_boards(boards)

        if not boards:
           return

        for channel in self.current_board.pwm_output:
            self.channel_list.addItem(str(channel))

    def declare_components(self) -> None:
        
        super().declare_components()

        self.sb_pulse_duration_msec = LabeledDoubleSpinBox()
        self.sb_pulse_duration_msec.setText('Pulse duration (msec)')
        self.sb_pulse_duration_msec.setRange(1, 1_000.0)
        self.sb_pulse_duration_msec.setValue(self.pulse_duration_msec)
        self.sb_pulse_duration_msec.valueChanged.connect(self.state_changed)       
        
        self.sb_duty_cycle = LabeledDoubleSpinBox()
        self.sb_duty_cycle.setText('Duty cycle')
        self.sb_duty_cycle.setRange(0, 1.0)
        self.sb_duty_cycle.setSingleStep(0.01)
        self.sb_duty_cycle.setValue(self.duty_cycle)
        self.sb_duty_cycle.valueChanged.connect(self.state_changed)       
    
    def layout_components(self) -> None:
        
        super().layout_components()
        self.main_layout.addWidget(self.sb_pulse_duration_msec)
        self.main_layout.addWidget(self.sb_duty_cycle)
        self.main_layout.addWidget(self.stop_widget)
      
    def on_board_id_change(self):
        # change available channels
        
        super().on_board_id_change()
        self.channel_list.clear()
        for channel in self.current_board.pwm_output:
            self.channel_list.addItem(str(channel))

        self.state_changed.emit()

    def get_state(self) -> Dict:
        state = super().get_state()
        state['pulse_duration_msec'] = self.sb_pulse_duration_msec.value()
        state['duty_cycle'] = self.sb_duty_cycle.value()
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
            key = 'duty_cycle',
            setter = self.sb_duty_cycle.setValue,
            default = self.duty_cycle,
            cast = float
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:

        super().from_protocol_item(protocol_item)
        if isinstance(protocol_item, PWM_Pulse):
            self.sb_pulse_duration_msec.setValue(protocol_item.pulse_duration_msec)
            self.sb_duty_cycle.setValue(protocol_item.duty_cycle)

    def to_protocol_item(self) -> PWM_Pulse:

        channel_list_widget = self.channel_list.selectedItems()
        channels = [int(widget.text()) for widget in channel_list_widget]
    
        return PWM_Pulse(
            board_type = self.current_board_type,
            board_id = self.current_board.id,
            channels = channels,
            pulse_duration_msec = self.sb_pulse_duration_msec.value(),
            duty_cycle = self.sb_duty_cycle.value(),
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
    window = PWM_PulseWidget(
        boards = boards,
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
    
    pwm_pulse = window.to_protocol_item()
    print(pwm_pulse.start())