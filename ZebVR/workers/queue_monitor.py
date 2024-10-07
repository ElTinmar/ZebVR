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
            queues : Dict[QueueLike, str],
            refresh_interval_seconds: int = 0.1,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.queues = queues
        self.widgets = []
        self.refresh_interval_seconds = refresh_interval_seconds

    def initialize(self) -> None:

        super().initialize()
        
        self.app = QApplication([])
        self.window = QueueMonitorWidget()

        for queue, name in self.queues.items():
            queue_widget = QueueWidget(name)
            self.widgets.append(queue_widget)
            self.window.add_progress_bar(queue_widget)

        self.window.show()

    def process_data(self, data) -> None:

        self.app.processEvents()
        self.app.sendPostedEvents()

        for queue, widget in zip(self.queues.keys(), self.widgets):
            queue.queue.load_array_metadata() # hum
            widget.set_state(queue.qsize(), queue.get_num_items())

        time.sleep(self.refresh_interval_seconds)

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        pass
        