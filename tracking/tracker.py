from .body import BodyTracker
from .eyes import EyesTracker
from .tail import TailTracker 
from .prey import PreyTracker 
from core.abstractclasses import Tracker
from numpy.typing import NDArray
from typing import List


class TrackerCollection:
    def __init__(
        self,
        tracker_list: List[Tracker],
    ) -> None:
        
        self.trackers

    def track(self, image: NDArray) -> Tracking:
        if self.body_tracker:
        body_tracking = self.body_tracker.track(image)
        eyes_tracking = self.eyes_tracker.track(image)
        tail_tracking = self.tail_tracker.track(image)
        prey_tracking = self.prey_tracker.track(image)
        return