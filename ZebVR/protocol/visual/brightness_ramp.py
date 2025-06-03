from ...protocol import Stim, ProtocolItem, VisualProtocolItemWidget, StopWidget, Debouncer
from typing import Tuple, Dict
from qt_widgets import LabeledDoubleSpinBox
from PyQt5.QtWidgets import (
    QGroupBox, 
    QVBoxLayout,
    QApplication, 
)
from ...utils import set_from_dict
from ..default import DEFAULT

class BrightnessRamp(ProtocolItem):

    STIM_SELECT = Stim.BRIGHTNESS_RAMP

    def __init__(
            self, 
            ramp_start_percent: float = DEFAULT['ramp_start_percent'],
            ramp_stop_percent: float = DEFAULT['ramp_stop_percent'],
            ramp_duration_sec: float = DEFAULT['ramp_duration_sec'],
            foreground_color: Tuple[float, float, float, float] = DEFAULT['foreground_color'],
            background_color: Tuple[float, float, float, float] = DEFAULT['background_color'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.ramp_start_percent = ramp_start_percent
        self.ramp_stop_percent = ramp_stop_percent
        self.ramp_duration_sec = ramp_duration_sec
        self.foreground_color = foreground_color 
        self.background_color = background_color 

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'ramp_start_percent': self.ramp_start_percent,
            'ramp_stop_percent': self.ramp_stop_percent,
            'ramp_duration_sec': self.ramp_duration_sec,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color
        }
        return command
    
class BrightnessRampWidget(VisualProtocolItemWidget):
    ...