from ..protocol_item import Stim, ProtocolItem, ProtocolItemWidget
from typing import Tuple, Dict

class PreyCapture(ProtocolItem):

    STIM_SELECT = Stim.Visual.PREY_CAPTURE

    def __init__(
            self, 
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            n_preys: int = 50,
            prey_speed_mm_s: float = 0.75,
            prey_radius_mm: float = 0.25,
            *args,
            **kwargs   
        ) -> None:

        super().__init__(*args, **kwargs)
        self.foreground_color = foreground_color 
        self.background_color = background_color
        self.n_preys = n_preys
        self.prey_speed_mm_s = prey_speed_mm_s 
        self.prey_radius_mm = prey_radius_mm

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'n_preys': self.n_preys,
            'prey_speed_mm_s': self.prey_speed_mm_s,
            'prey_radius_mm': self.prey_radius_mm
        }
        return command 

class PreyCaptureWidget(ProtocolItemWidget):
    ...