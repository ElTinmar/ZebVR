from ZebVR.protocol import Stim, AudioProtocolItem, AudioProtocolItemWidget, StopWidget, Debouncer
from typing import Dict
from qtpy.QtWidgets import (
    QApplication, 
)

class Silence(AudioProtocolItem):

    STIM_SELECT = Stim.SILENCE
    
    def start(self) -> Dict:

        command = super().start()
        command.update({'stim_select': self.STIM_SELECT})
        return command
    
class SilenceWidget(AudioProtocolItemWidget):

    def layout_components(self) -> None:
        
        super().layout_components()
        self.main_layout.addWidget(self.stop_widget)

    def to_protocol_item(self) -> Silence:
        return Silence(
            name = self.stim_name.text(),
            stop_condition = self.stop_widget.to_stop_condition()
        )

if __name__ == '__main__':

    app = QApplication([])
    window = SilenceWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
    