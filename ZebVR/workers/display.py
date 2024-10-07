from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional
import time
from PyQt5.QtWidgets import QApplication
from ZebVR.widgets import DisplayWidget

class Display(WorkerNode):

    def __init__(
            self, 
            fps: int = 30,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.fps = fps
        self.prev_time = 0
        self.first_timestamp = 0

    def initialize(self) -> None:

        super().initialize()
        
        self.app = QApplication([])
        self.window = DisplayWidget()
        self.window.show()

    def process_data(self, data) -> NDArray:

        self.app.processEvents()
        self.app.sendPostedEvents()
        
        if data is not None:

            if self.first_timestamp == 0:
                self.first_timestamp = data['timestamp']

            # restrict update freq to save resources
            if time.monotonic() - self.prev_time > 1/self.fps:

                self.window.set_state(
                    index = data['index'],
                    timestamp = round((data['timestamp'] - self.first_timestamp)*1e-9,3),
                    image = data['image']
                )

                self.prev_time = time.monotonic()

            return data

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        pass
        