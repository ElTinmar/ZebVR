from dagline import WorkerNode
from ipc_tools import QueueLike
from numpy.typing import NDArray
from typing import Dict, Optional
from PyQt5.QtWidgets import QApplication
from ZebVR.widgets import QueueWidget, QueueMonitorWidget
from typing import List
import time

class QueueMonitor(WorkerNode):

    def __init__(
            self, 
            queues : List[QueueLike],
            refresh_interval_seconds: int = 0.1,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.queues = queues
        self.refresh_interval_seconds = refresh_interval_seconds

    def initialize(self) -> None:

        super().initialize()
        
        self.app = QApplication([])
        self.window = QueueMonitorWidget()
        for q in self.queues:
            queue_widget = QueueWidget()
            self.window.add_progress_bar(queue_widget)
        self.window.show()

    def process_data(self, data) -> NDArray:
        self.app.processEvents()
        self.app.sendPostedEvents()
        time.sleep(self.refresh_interval_seconds)

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        pass
        