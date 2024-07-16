from video_tools import BackgroundSubtractor
from dagline import WorkerNode
from typing import Any

class BackgroundSubWorker(WorkerNode):

    def __init__(self, sub: BackgroundSubtractor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sub = sub

    def initialize(self) -> None:
        super().initialize()
        self.sub.initialize()

    def process_data(self, data):
        if data is not None:
            index, timestamp, image = data
            res = self.sub.subtract_background(image)
            return (index, timestamp, res)

    def process_metadata(self, metadata) -> Any:
        pass