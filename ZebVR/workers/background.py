from video_tools import BackgroundSubtractor
from dagline import WorkerNode
from typing import Any
import numpy as np

class BackgroundSubWorker(WorkerNode):

    def __init__(self, sub: BackgroundSubtractor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sub = sub

    def initialize(self) -> None:
        super().initialize()
        self.sub.initialize()

    def process_data(self, data):
        if data is not None:
            background_sub = self.sub.subtract_background(data['image'])
            res = np.array(
                (data['index'], data['timestamp'], background_sub),
                dtype=([
                    ('index', int),
                    ('timestamp', np.float32),
                    ('image', background_sub.dtype, background_sub.shape)
                ])
            )            
            return res

    def process_metadata(self, metadata) -> Any:
        pass