from ...protocol import (
    Stim, 
    ProtocolItem, 
    VisualProtocolItem,
    VisualProtocolItemWidget, 
    StopWidget, 
    Debouncer
)
from typing import Tuple, Dict
from PyQt5.QtWidgets import (
    QApplication, 
)
from ..default import DEFAULT

class Dark(VisualProtocolItem):

    STIM_SELECT = Stim.DARK

    def __init__(
            self,
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'closed_loop': self.closed_loop
        }
        return command
    
class DarkWidget(VisualProtocolItemWidget):

    def __init__(
            self,
            *args, 
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()
        self.chb_closed_loop.setChecked(False)
        self.chb_closed_loop.setVisible(False)

    def layout_components(self) -> None:
        
        super().layout_components()
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:
        return super().get_state()
    
    def set_state(self, state: Dict) -> None:
        super().set_state(state)

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:
        super().from_protocol_item(protocol_item)

    def to_protocol_item(self) -> Dark:
        
        foreground_color = (
            self.sb_foreground_color_R.value(), 
            self.sb_foreground_color_G.value(),
            self.sb_foreground_color_B.value(),
            self.sb_foreground_color_A.value()
        )
        background_color = (
            self.sb_background_color_R.value(), 
            self.sb_background_color_G.value(),
            self.sb_background_color_B.value(),
            self.sb_background_color_A.value()
        )
        closed_loop = self.chb_closed_loop.isChecked()
        protocol = Dark(
            foreground_color = foreground_color,
            background_color = background_color,
            closed_loop = closed_loop,
            stop_condition = self.stop_widget.to_stop_condition()
        )
        return protocol
    
if __name__ == '__main__':

    app = QApplication([])
    window = DarkWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
    
