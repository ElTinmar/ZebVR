from .lightcrafter_4500.configure import configure
from core.abstractclasses import Projector

class LCR4500(Projector):
    def __init__(self, monitor_id) -> None:
        super().__init__(monitor_id)
        configure()

