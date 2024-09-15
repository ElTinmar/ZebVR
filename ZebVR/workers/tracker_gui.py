import time
from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional
from PyQt5.QtWidgets import QApplication
from ZebVR.widgets import TrackerWidget
from pathlib import Path

class TrackerGui(WorkerNode):

    def __init__(
            self,
            n_tracker_workers: int,
            settings_file: Path = Path('tracking.json'),
            *args,
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.n_tracker_workers = n_tracker_workers 
        self.settings_file = settings_file

    def initialize(self) -> None:
        super().initialize()
        
        self.app = QApplication([])
        self.window = TrackerWidget(settings_file = self.settings_file)
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
