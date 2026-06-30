from ...protocol import (
    Stim, 
    ProtocolItem, 
    VisualProtocolItem,
    VisualProtocolItemWidget, 
    StopWidget, 
    Debouncer
)
from typing import Tuple, Dict
from qtpy.QtWidgets import (
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
        command = super().start()
        command.update({'stim_select': self.STIM_SELECT})
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
        self.cb_coordinate_system.setVisible(False)

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
        return Dark(**self._get_protocol_kwargs())
    
if __name__ == '__main__':

    app = QApplication([])
    window = DarkWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
    
