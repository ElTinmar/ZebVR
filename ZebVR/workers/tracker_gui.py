import time
from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional
from PyQt5.QtWidgets import QApplication
from ZebVR.widgets import TrackerWidget

class TrackerGui(WorkerNode):

    def __init__(
            self,
            animal_tracking_param: Dict,
            body_tracking_param: Dict,
            eyes_tracking_param: Dict,
            tail_tracking_param: Dict,
            body_tracking: bool,
            eyes_tracking: bool,
            tail_tracking: bool,
            n_tracker_workers: int,
            *args,
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.animal_tracking_param = animal_tracking_param 
        self.body_tracking_param = body_tracking_param 
        self.eyes_tracking_param = eyes_tracking_param 
        self.tail_tracking_param = tail_tracking_param 
        self.n_tracker_workers = n_tracker_workers 
        self.body_tracking = body_tracking
        self.eyes_tracking = eyes_tracking
        self.tail_tracking = tail_tracking

    def initialize(self) -> None:
        super().initialize()
        
        self.app = QApplication([])
        self.window = TrackerWidget(
            self.animal_tracking_param, 
            self.body_tracking_param, 
            self.eyes_tracking_param, 
            self.tail_tracking_param,  
            self.body_tracking,
            self.eyes_tracking,
            self.tail_tracking
        )
        self.window.show()

    def process_data(self, data: None) -> NDArray:
        self.app.processEvents()
        self.app.sendPostedEvents()
        time.sleep(0.01)

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        # send tracking controls
        if self.window.is_updated():
            res = {}
            for i in range(self.n_tracker_workers):
                res[f'tracker_control_{i}'] = self.window.get_state()
            self.window.set_updated(False)
            return res
