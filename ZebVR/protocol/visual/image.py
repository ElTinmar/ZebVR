from ...protocol import Stim, ProtocolItem, VisualProtocolItemWidget, StopWidget, Debouncer
from typing import Tuple, Dict
from qt_widgets import LabeledDoubleSpinBox
from PyQt5.QtWidgets import (
    QGroupBox, 
    QVBoxLayout,
    QApplication, 
)
from ...utils import set_from_dict

class Image(ProtocolItem):

    STIM_SELECT = Stim.Visual.IMAGE

    def __init__(
            self, 
            image_path: str,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.image_path = image_path
        self.foreground_color = foreground_color
        self.background_color = background_color 

    def start(self) -> Dict:

        super().start()

        command = {
            'stim_select': self.STIM_SELECT,
            'image_path': str(self.image_path),
            'foreground_color': self.foreground_color,
            'background_color': self.background_color
        }
        return command
    
class ImageWidget(ProtocolItemWidget):
    ...