from tracker import (
    GridAssignment, MultiFishTracker, MultiFishTracker_CPU,
    AnimalTracker_CPU,  AnimalTrackerParamTracking,
    BodyTracker_CPU, BodyTrackerParamTracking
)
from dagline import WorkerNode
import numpy as np
from numpy.typing import NDArray
from typing import Any, Dict
from ZebVR.config import CAM_WIDTH, CAM_HEIGHT, N_TRACKER_WORKERS

class TrackerWorker(WorkerNode):
    
    def __init__(self, tracker: MultiFishTracker, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tracker = tracker

    def initialize(self) -> None:
        super().initialize()

        # try to trigger numba compilation during init phase (doesn't work right now)
        # self.tracker.tail.track(np.zeros((100,100),dtype=np.float32), centroid=np.array([0,0]))

    def process_data(self, data: NDArray) -> Dict:
        try:
            index, timestamp, image = data
            tracking = self.tracker.track(image)
            res = {}
            k = tracking.animals.identities[0]
            res['stimulus'] = (index, timestamp, tracking.animals.centroids[k,:], tracking.body[k].heading[:,1])
            res['overlay'] = (index, timestamp, tracking)
            return res
        except:
            return None  
        
    def process_metadata(self, metadata) -> Any:
        # reveive tracker settings and update tracker
        for i in range(N_TRACKER_WORKERS):
            control = metadata[f'tracker_control_{i}']
            if control is not None: 
                self.tracker = MultiFishTracker_CPU(
                    max_num_animals=1,
                    accumulator=None, 
                    export_fullres_image=True,
                    downsample_fullres_export=0.25,
                    animal=AnimalTracker_CPU(
                        assignment=GridAssignment(LUT=np.zeros((CAM_HEIGHT,CAM_WIDTH), dtype=np.int_)), 
                        tracking_param=AnimalTrackerParamTracking(**control['animal_tracking'])
                    ),
                    body=BodyTracker_CPU(tracking_param=BodyTrackerParamTracking(**control['body_tracking'])),
                    eyes=None,
                    tail=None
                )
