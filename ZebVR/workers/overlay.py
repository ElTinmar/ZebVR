from tracker import  MultiFishOverlay
from dagline import WorkerNode
import time
from typing import Any, Dict

class OverlayWorker(WorkerNode):

    def __init__(self, overlay: MultiFishOverlay, fps: int = 30, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.overlay = overlay
        self.fps = fps
        self.prev_time = 0

    def process_data(self, data: Any) -> Dict:
        if data is not None:
            index, timestamp, tracking = data
            if time.monotonic() - self.prev_time > 1/self.fps:
                if tracking.animals.identities is not None:
                    overlay = self.overlay.overlay(tracking.image, tracking)
                    self.prev_time = time.monotonic()
                    return (index, timestamp, overlay)

    def process_metadata(self, metadata) -> Any:
        pass