from typing import Any, Dict, Optional
import numpy as np
from numpy.typing import NDArray
import time
import cv2

# TODO control this with a widget
ENABLE_KALMAN = False

from tracker import (
    SingleFishTracker, 
    SingleFishTracker_CPU,
    SingleFishTrackerParamTracking,
    AnimalTracker_CPU,
    AnimalTrackerKalman,  
    AnimalTrackerParamTracking,
    BodyTracker_CPU, 
    BodyTrackerKalman,
    BodyTrackerParamTracking,
    EyesTracker_CPU,
    EyesTrackerKalman,
    EyesTrackerParamTracking, 
    TailTracker_CPU,
    TailTrackerKalman,
    TailTrackerParamTracking,
)
from dagline import WorkerNode
from geometry import SimilarityTransform2D

class DummyTrackerWorker(WorkerNode):
    '''For open loop tracking, sends the centroid / main direction'''
    def __init__(
            self,
            tracker: SingleFishTracker, 
            centroid: NDArray,
            heading: NDArray,
            roi: NDArray,
            identity: int,
            *args, 
            **kwargs
        ):
        super().__init__(*args, **kwargs)

        x,y,w,h = roi
        self.origin = np.array((x,y))
        self.shape = (h,w)
        self.tracking = np.zeros(1, tracker.tracking_param.dtype)
        self.tracking['success'] = True
        self.tracking['body']['success'] = True
        self.tracking['body']['centroid_global'] = centroid + self.origin + np.array((w//2, h//2)) 
        self.tracking['body']['body_axes_global'] = heading
        self.indentity = identity

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
            (index, timestamp, self.tracking, self.origin, self.shape, self.indentity),
            dtype=np.dtype([
                ('index', int),
                ('timestamp', np.int64),
                ('tracking', self.tracking.dtype),
                ('origin', np.int32, (2,)),
                ('shape', np.int32, (2,)),
                ('identity', np.int32)
            ])
        )
        res['tracker_output_stim'] = msg
        return res
        
    def process_metadata(self, metadata) -> Any:
        pass
    
class TrackerWorker(WorkerNode):
    
    def __init__(
            self, 
            tracker: SingleFishTracker, 
            cam_fps: float,
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
        self.cam_fps = cam_fps
        self.n_tracker_workers = n_tracker_workers
        self.current_tracking = None

    def process_data(self, data: NDArray) -> Dict:

        if data is None:
            return None

        T = SimilarityTransform2D.translation(data['origin'][0], data['origin'][1])

        tracking = self.tracker.track(data['image'], None, T)
        
        msg = np.array(
            (data['index'], data['timestamp'], tracking, data['origin'], data['shape'], data['identity']),
            dtype=np.dtype([
                ('index', int),
                ('timestamp', np.int64),
                ('tracking', tracking.dtype),
                ('origin', np.int32, (2,)),
                ('shape', np.int32, (2,)),
                ('identity', np.int32),
            ])
        )

        res = {}    
        res['tracker_output_stim'] = msg # visual stimulus, TODO no need to send image, send only relevant info 
        res['tracker_output_overlay'] = msg
        res['tracker_output_saver'] = msg 
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
            
            print(control)
            
            if ENABLE_KALMAN:
                # TODO : parametrize this with a widget
                animal = AnimalTrackerKalman(
                    tracking_param=AnimalTrackerParamTracking(**control['animal_tracking']),
                    fps = self.cam_fps, 
                    model_order=2,
                    model_uncertainty=0.2,
                    measurement_uncertainty=1
                )
                
                body = eyes = tail = None

                if control['body_tracking_enabled']:
                    body = BodyTrackerKalman(
                        tracking_param=BodyTrackerParamTracking(**control['body_tracking']), 
                        fps = self.cam_fps, 
                        history_sec = 0.2,
                        model_order=2,
                        model_uncertainty=0.2,
                        measurement_uncertainty=1
                    )

                if control['eyes_tracking_enabled']:
                    eyes = EyesTrackerKalman(
                        tracking_param=EyesTrackerParamTracking(**control['eyes_tracking']),
                        fps = self.cam_fps, 
                        model_order=1,
                        model_uncertainty=0.2,
                        measurement_uncertainty=1
                    )

                if control['tail_tracking_enabled']:
                    tail = TailTrackerKalman(
                        tracking_param=TailTrackerParamTracking(**control['tail_tracking']),
                        fps = self.cam_fps, 
                        model_order=2,
                        model_uncertainty=1,
                        measurement_uncertainty=1
                    )
            else:
                animal = AnimalTracker_CPU(
                    tracking_param=AnimalTrackerParamTracking(**control['animal_tracking']),
                )
                
                body = eyes = tail = None

                if control['body_tracking_enabled']:
                    body = BodyTracker_CPU(
                        tracking_param=BodyTrackerParamTracking(**control['body_tracking']), 
                        fps = self.cam_fps
                    )

                if control['eyes_tracking_enabled']:
                    eyes = EyesTracker_CPU(
                        tracking_param=EyesTrackerParamTracking(**control['eyes_tracking']),
                    )

                if control['tail_tracking_enabled']:
                    tail = TailTracker_CPU(
                        tracking_param=TailTrackerParamTracking(**control['tail_tracking']),
                    )
            
            self.tracker = SingleFishTracker_CPU(
                SingleFishTrackerParamTracking(
                    animal = animal,
                    body = body,
                    eyes = eyes,
                    tail = tail
                )
            )
        
        # send tracking as metadata
        if self.current_tracking is None:
            return
        
        fish_centroid = np.zeros((2,), dtype=float)
        
        try:
            tracking = self.current_tracking['tracking']

            if tracking['body'] is not None:
                fish_centroid[:] = tracking['body']['centroid_global']
            else:
                fish_centroid[:] = tracking['animals']['centroid_global']

        except KeyError:
            return None
        
        except TypeError:
            return None
        
        except ValueError:
            return None
        
        res = {}    
        res['tracker_metadata'] = fish_centroid.astype(int)
        return res

