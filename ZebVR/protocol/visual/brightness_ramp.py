from ..protocol_item import Stim, ProtocolItem, ProtocolItemWidget
from typing import Tuple, Dict

class BrightnessRamp(ProtocolItem):

    STIM_SELECT = Stim.Visual.BRIGHTNESS_RAMP

    def __init__(
            self, 
            brightness_start_percent: float,
            brightness_stop_percent: float,
            duration_sec: float,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.brightness_start_percent = brightness_start_percent
        self.brightness_stop_percent = brightness_stop_percent
        self.duration_sec = duration_sec
        self.foreground_color = foreground_color 
        self.background_color = background_color 

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'brightness_start_percent': self.brightness_start_percent,
            'brightness_stop_percent': self.brightness_stop_percent,
            'duration_sec': self.duration_sec,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color
        }
        return command
    
class BrightnessRampWidget(ProtocolItemWidget):
    ...