from core.abstractclasses import Tracker
from numpy.typing import NDArray
from typing import List
import numpy as np


class TrackerCollection(Tracker):
    def __init__(
        self,
        tracker_list: List[Tracker],
    ) -> None:
        
        self.tracker_list = tracker_list

    def track(self, image: NDArray) -> List[NDArray]:
        tracking = [] 
        for tracker in self.tracker_list:
            tracking.append(tracker.track(image))
        return tracking

    def tracking_overlay(self, image: NDArray) -> NDArray:

        overlay = np.zeros(
            (image.shape[0],image.shape[1],3), 
            dtype=np.single
        )
        
        for tracker in self.tracker_list:
            overlay += tracker.tracking_overlay(image)

        return overlay