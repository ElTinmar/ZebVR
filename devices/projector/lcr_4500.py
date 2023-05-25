from .lightcrafter_4500.configure import configure
from .opencv_projector import CVProjector

class LCR4500(CVProjector):
    def __init__(self, monitor_id) -> None:
        super().__init__(monitor_id)
        configure()

