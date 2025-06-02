from ..protocol_item import Stim, ProtocolItem, ProtocolItemWidget
from typing import Tuple, Dict

class Phototaxis(ProtocolItem):

    STIM_SELECT = Stim.Visual.PHOTOTAXIS

    def __init__(
            self, 
            phototaxis_polarity: int,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.phototaxis_polarity = phototaxis_polarity
        self.foreground_color = foreground_color
        self.background_color = background_color 

    def start(self) -> Dict:

        super().start()

        command = {
            'stim_select': self.STIM_SELECT,
            'phototaxis_polarity': self.phototaxis_polarity,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color
        }
        return command
    
class PhototaxisWidget(ProtocolItemWidget):
    ...