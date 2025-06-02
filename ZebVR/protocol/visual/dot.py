from ..protocol_item import Stim, ProtocolItem, ProtocolItemWidget
from typing import Tuple, Dict

class Dot(ProtocolItem):

    STIM_SELECT = Stim.Visual.DOT

    def __init__(
            self, 
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            dot_center_mm: Tuple[float, float],
            dot_radius_mm: float,
            *args,
            **kwargs   
        ) -> None:

        super().__init__(*args, **kwargs)
        self.foreground_color = foreground_color 
        self.background_color = background_color
        self.dot_center_mm = dot_center_mm
        self.dot_radius_mm = dot_radius_mm 

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'dot_center_mm': self.dot_center_mm,
            'dot_radius_mm': self.dot_radius_mm,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
        }
        return command 

class FollowingDot(ProtocolItem):
    STIM_SELECT = Stim.Visual.FOLLOWING_DOT
    
class DotWidget(ProtocolItemWidget):
    ...

class FollowingDotWidget(DotWidget):
    ...