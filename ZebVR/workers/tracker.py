from tracker import (
    GridAssignment, LinearSumAssignment,
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
from typing import Any, Dict, Optional
import time
from geometry import SimilarityTransform2D

# TODO fix that
class DummyTrackerWorker(WorkerNode):
    '''For open loop tracking, sends the centroid / main direction'''
    def __init__(
            self,
            tracker: MultiFishTracker, 
            centroid: NDArray,
            heading: NDArray,
            *args, 
            **kwargs
        ):
        super().__init__(*args, **kwargs)

        self.tracking = np.zeros(1, tracker.tracking_param.dtype())
        self.tracking['body'][0]['centroid_global'] = centroid
        self.tracking['body'][0]['body_axes_global'] = heading

    def initialize(self) -> None:
        super().initialize()

    def process_data(self, data: Optional[NDArray]) -> Dict:
        
        index = 0
        timestamp = 0
        if data is not None:
            index = data['index']
            timestamp = data['timestamp']
        else:
            time.sleep(0.010)
        
        res = {}
        msg = np.array(
            (index, timestamp, self.tracking),
            dtype=np.dtype([
                ('index', int),
                ('timestamp', np.float64),
                ('tracking', self.tracking.dtype)
            ])
        )
        res['tracker_output1'] = msg
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
        self.current_tracking = None
        
    def initialize(self) -> None:
        super().initialize()

        # try to trigger numba compilation during init phase (doesn't work right now)
        # self.tracker.tail.track(np.zeros((100,100),dtype=np.float32), centroid=np.array([0,0]))

    def process_data(self, data: NDArray) -> Dict:

        if data is None:
            return None

        T = SimilarityTransform2D.translation(data['origin'][0],data['origin'][1])

        tracking = self.tracker.track(data['image'], None, T)

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
        res['tracker_output1'] = msg # visual stimulus, TODO no need to send image, send only relevant info 
        res['tracker_output2'] = msg # overlay    
        self.current_tracking = msg

        return res
        
    def process_metadata(self, metadata) -> Any:

        # handle control input
        for i in range(self.n_tracker_workers):
            
            try:
                control = metadata[f'tracker_control_{i}']
            except KeyError:
                continue

            if control is None:
                continue
            
            if control['assignment'] == 'ROI':
                assignment = GridAssignment(
                    LUT=np.zeros((self.cam_height, self.cam_width), dtype=np.int_), # TODO fix that, add a ROI selection tool
                    num_animals = control['animal_tracking']['num_animals']
                )
            elif control['assignment'] == 'Hungarian':
                assignment = LinearSumAssignment(
                    distance_threshold = 20, # TODO fix that, add a widget
                    num_animals = control['animal_tracking']['num_animals']
                )
            else:
                break
            
            animal = AnimalTracker_CPU(
                assignment=assignment, 
                tracking_param=AnimalTrackerParamTracking(**control['animal_tracking'])
            )
            
            if control['body_tracking_enabled']:
                body = BodyTracker_CPU(tracking_param=BodyTrackerParamTracking(**control['body_tracking']))
            else:
                body = None

            if control['eyes_tracking_enabled']:
                eyes = EyesTracker_CPU(tracking_param=EyesTrackerParamTracking(**control['eyes_tracking']))
            else:
                eyes = None

            if control['tail_tracking_enabled']:
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
        
        # send tracking as metadata
        if self.current_tracking is None:
            return
        
        fish_centroid = np.zeros((2,), dtype=float)
        
        try:
            tracking = self.current_tracking['tracking']

            # TODO choose animal
            k = 0

            if tracking['body'][k] is not None:
                fish_centroid[:] = tracking['body'][k]['centroid_global']
            else:
                fish_centroid[:] = tracking['animals']['centroid_global'][k,:]

        except KeyError:
            return None
        except TypeError:
            return None
        except ValueError:
            return None
        
        res = {}    
        res['tracker_metadata'] = fish_centroid.astype(int)
        return res

