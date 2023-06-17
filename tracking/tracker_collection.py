from core.abstractclasses import Tracker
from numpy.typing import NDArray
from typing import List
from tracking.body.body_tracker import BodyTracker
from tracking.eyes.eyes_tracker import EyesTracker
from tracking.tail.tail_tracker import TailTracker
from tracking.prey.prey_tracker import PreyTracker
from core.dataclasses import TrackingCollection

class TrackerCollection(Tracker):
    def __init__(
        self,
        body_tracker: BodyTracker,
        tracker_list: List[Tracker],
    ) -> None:
        
        self.body_tracker = body_tracker
        self.tracker_list = tracker_list

    def track(self, image: NDArray) -> TrackingCollection:

        body_tracking = self.body_tracker.track(image)
        tracking = TrackingCollection(body = body_tracking)

        for tracker in self.tracker_list:
            if isinstance(tracker, TailTracker):
                if body_tracking is not None:
                    t = tracker.track(image, body_tracking.centroid, body_tracking.heading)
                    tracking.tail = t
            elif isinstance(tracker, EyesTracker):
                if body_tracking is not None:
                    t = tracker.track(image, body_tracking.centroid, body_tracking.heading)
                    tracking.eyes = t
            elif isinstance(tracker, PreyTracker):
                t = tracker.track(image)
                tracking.prey = t
            else:
                raise(TypeError("Unknown tracking type"))
            
        return tracking
    