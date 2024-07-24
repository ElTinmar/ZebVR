from dagline import WorkerNode
import time
from numpy.typing import NDArray
from typing import Dict, Optional
from PyQt5.QtWidgets import QApplication
from ZebVR.widgets import CameraWidget

class CameraGui(WorkerNode):

    def initialize(self) -> None:
        super().initialize()
        
        self.app = QApplication([])
        self.window = CameraWidget()
        self.window.show()

    def process_data(self, data: None) -> NDArray:
        self.app.processEvents()
        self.app.sendPostedEvents()
        time.sleep(0.01)

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:    
        # receive cam inof
        info = metadata['camera_info']
        if info is not None: 
            self.block_signals(True)
            for c in self.controls:
                spinbox = getattr(self, c + '_spinbox')
                spinbox.setValue(info[c]['value'])
                spinbox.setRange(info[c]['min'], info[c]['max'])
                spinbox.setSingleStep(info[c]['increment'])
            self.block_signals(False)

        # send only one message when things are changed
        if self.window.is_updated():
            res = {}
            res['camera_control'] = self.window.get_state()
            self.window.set_updated(False)
            return res       
        else:
            return None