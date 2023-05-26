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
        self.curr_tracking = None

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
            
        self.curr_tracking = tracking
        return self.curr_tracking

    def tracking_overlay(self, image: NDArray) -> NDArray:

        overlay = np.zeros(
            (image.shape[0],image.shape[1],3), 
            dtype=np.single
        )
        
        for tracker in self.tracker_list:
            overlay += tracker.tracking_overlay(image)

        return overlay