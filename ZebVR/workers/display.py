from dagline import WorkerNode
from numpy.typing import NDArray
import time
from typing import Any
import cv2

class DisplayWorker(WorkerNode):

    def __init__(self, fps: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fps = fps
        self.prev_time = 0

    def initialize(self) -> None:
        super().initialize()
        cv2.namedWindow('display')
    
    def cleanup(self) -> None:
        super().cleanup()
        cv2.destroyAllWindows()

    def process_data(self, data: NDArray) -> None:
        if data is not None:
            index, timestamp, image = data
            if time.monotonic() - self.prev_time > 1/self.fps:
                cv2.imshow('display', image) # NOT data[0]
                cv2.waitKey(1)
                self.prev_time = time.monotonic()

    def process_metadata(self, metadata) -> Any:
        pass