from .body import BodyTracker
from .eyes import EyesTracker
from .tail import TailTracker 
from .prey import PreyTracker 
from core.abstractclasses import Tracker
from numpy.typing import NDArray
from typing import List


class TrackerCollection(Tracker):
    def __init__(
        self,
        tracker_list: List[Tracker],
    ) -> None:
        
        self.tracker_list = tracker_list

    def track(self, image: NDArray) -> NDArray:
        tracking = [] 
        for tracker in self.tracker_list:
            tracking.append(tracker.track(image))
        return tracking