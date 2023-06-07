from core.abstractclasses import Tracker
from numpy.typing import NDArray
from typing import List
import numpy as np
from core.dataclasses import TrackingCollection, BodyTracking, EyeTracking, TailTracking, PreyTracking

class TrackerCollection(Tracker):
    def __init__(
        self,
        tracker_list: List[Tracker],
    ) -> None:
        
        self.tracker_list = tracker_list

    def track(self, image: NDArray) -> TrackingCollection:
        tracking = TrackingCollection()

        for tracker in self.tracker_list:
            t = tracker.track(image)
            if t is not None:
                if isinstance(t, BodyTracking):
                    tracking.body = t
                elif isinstance(t, EyeTracking):
                    tracking.eyes = t
                elif isinstance(t, TailTracking):
                    tracking.tail = t
                elif isinstance(t, PreyTracking):
                    tracking.prey = t
                else:
                    raise(TypeError("Unknown tracking type"))
            
        return tracking
    