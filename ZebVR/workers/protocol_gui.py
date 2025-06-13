from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional, Tuple
import time
from ..widgets import StimWidget
from ..protocol import Debouncer
from PyQt5.QtWidgets import QApplication

class StimGUI(WorkerNode):
    
    DEFAULT_DEBOUNCER_LENGTH = 5

    def __init__(
            self, 
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)

        self.debouncer = Debouncer(self.DEFAULT_DEBOUNCER_LENGTH)

    def initialize(self) -> None:
        super().initialize()
        self.app = QApplication([])
        self.window = StimWidget(
            debouncer = self.debouncer,
        )
        #self.window.stack.currentWidget().stop_widget.setVisible(False)
        self.window.show()
    
    def process_data(self, data: None) -> NDArray:
        self.app.processEvents()
        self.app.sendPostedEvents()
        time.sleep(0.01)

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        # send only one message when things are changed
        if self.window.is_updated():
            res = {}
            res['stim_control'] = self.window.get_state()
            res['audio_stim_control'] = self.window.get_state()
            self.window.set_updated(False)
            return res       
        else:
            return None
        