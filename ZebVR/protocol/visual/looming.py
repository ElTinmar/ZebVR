from ..protocol_item import Stim, ProtocolItem, ProtocolItemWidget
from typing import Tuple, Dict

class Looming(ProtocolItem):

    STIM_SELECT = Stim.Visual.LOOMING

    def __init__(
            self, 
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            looming_center_mm: Tuple[float, float],
            looming_period_sec: float,
            looming_expansion_time_sec: float,
            looming_expansion_speed_mm_per_sec: float,
            *args,
            **kwargs   
        ) -> None:

        super().__init__(*args, **kwargs)
        self.foreground_color = foreground_color 
        self.background_color = background_color
        self.looming_center_mm = looming_center_mm
        self.looming_period_sec = looming_period_sec 
        self.looming_expansion_time_sec = looming_expansion_time_sec
        self.looming_expansion_speed_mm_per_sec = looming_expansion_speed_mm_per_sec

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'looming_center_mm': self.looming_center_mm,
            'looming_period_sec': self.looming_period_sec,
            'looming_expansion_time_sec': self.looming_expansion_time_sec,
            'looming_expansion_speed_mm_per_sec': self.looming_expansion_speed_mm_per_sec,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color
        }
        return command 

class FollowingLooming(Looming):
    STIM_SELECT = Stim.Visual.FOLLOWING_LOOMING

class LoomingWidget(ProtocolItem):
    ...

class FollowingLoomingWidget(LoomingWidget):
    ...