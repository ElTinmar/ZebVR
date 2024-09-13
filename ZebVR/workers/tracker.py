from tracker import (
    GridAssignment, 
    MultiFishTracker, 
    MultiFishTracker_CPU,
    MultiFishTrackerParamTracking,
    AnimalTracker_CPU,  
    AnimalTrackerParamTracking,
    BodyTracker_CPU, 
    BodyTrackerParamTracking,
    EyesTracker_CPU,
    EyesTrackerParamTracking, 
    TailTracker_CPU,
    TailTrackerParamTracking,
)
from dagline import WorkerNode
import numpy as np
from numpy.typing import NDArray
from typing import Any, Dict
import time

# TODO fix that
class DummyTrackerWorker(WorkerNode):
    '''For open loop tracking, sends the centroid / main direction'''
    def __init__(
            self,
            heading: NDArray,
            centroid: NDArray,
            *args, 
            **kwargs
        ):
        super().__init__(*args, **kwargs)

        self.heading = heading
        self.centroid = centroid

    def initialize(self) -> None:
        super().initialize()

    def process_data(self, data: NDArray) -> Dict:

        index = -1
        timestamp = -1
        res = {}
        res['stimulus'] = (index, timestamp, self.tracking)

        time.sleep(0.010)

        return res
        
    def process_metadata(self, metadata) -> Any:
        pass
    
class TrackerWorker(WorkerNode):
    
    def __init__(
            self, 
            tracker: MultiFishTracker, 
            cam_width: int,
            cam_height: int,
            n_tracker_workers: int,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.tracker = tracker
        self.cam_width = cam_width 
        self.cam_height = cam_height
        self.n_tracker_workers = n_tracker_workers
        
    def initialize(self) -> None:
        super().initialize()

        # try to trigger numba compilation during init phase (doesn't work right now)
        # self.tracker.tail.track(np.zeros((100,100),dtype=np.float32), centroid=np.array([0,0]))

    def process_data(self, data: NDArray) -> Dict:

        if data is None:
            return None

        tracking = self.tracker.track(data['image'])
        
        if tracking is None:
            return None
        
        msg = np.array(
            (data['index'], data['timestamp'], tracking),
            dtype=np.dtype([
                ('index', int),
                ('timestamp', np.float64),
                ('tracking', tracking.dtype)
            ])
        )

        res = {}    
        res['stimulus'] = msg
        res['overlay'] = msg
        return res
        
    def process_metadata(self, metadata) -> Any:

        for i in range(self.n_tracker_workers):
            
            try:
                control = metadata[f'tracker_control_{i}']
            except KeyError:
                control = None

            if control is None:
                return 

            animal = AnimalTracker_CPU(
                assignment=GridAssignment(LUT=np.zeros((self.cam_height, self.cam_width), dtype=np.int_)), 
                tracking_param=AnimalTrackerParamTracking( 
                    source_image_shape = (self.cam_height,self.cam_width), 
                    **control['animal_tracking']
                )
            )
            
            if control['body']:
                body = BodyTracker_CPU(tracking_param=BodyTrackerParamTracking(**control['body_tracking']))
            else:
                body = None

            if control['eyes']:
                eyes = EyesTracker_CPU(tracking_param=EyesTrackerParamTracking(**control['eyes_tracking']))
            else:
                eyes = None

            if control['tail']:
                tail = TailTracker_CPU(tracking_param=TailTrackerParamTracking(**control['tail_tracking']))
            else:
                tail = None  
            
            self.tracker = MultiFishTracker_CPU(
                MultiFishTrackerParamTracking(
                    accumulator=None,
                    animal=animal,
                    body=body,
                    eyes=eyes,
                    tail=tail
                )
            )

