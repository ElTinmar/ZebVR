from typing import Any, Dict
import numpy as np
from numpy.typing import NDArray
from ZebVR.utils.tracker_from_json import single_fish_tracker, head_embedded_tracker

from tracker import Tracker
from dagline import WorkerNode
from geometry import SimilarityTransform2D

class TrackerWorker(WorkerNode):
    
    def __init__(
            self, 
            tracker: Tracker, 
            background_image: np.ndarray,
            cam_fps: float,
            cam_width: int,
            cam_height: int,
            n_tracker_workers: int,
            head_embedded: bool = False,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.tracker = tracker
        self.background_image = background_image
        self.cam_width = cam_width 
        self.cam_height = cam_height
        self.cam_fps = cam_fps
        self.n_tracker_workers = n_tracker_workers
        self.head_embedded = head_embedded
        self.current_tracking = None

    def process_data(self, data: NDArray) -> Dict:

        if data is None:
            return None

        T = SimilarityTransform2D.translation(data['origin'][0], data['origin'][1])

        background = self.background_image[
            data['origin'][1]:data['origin'][1]+data['shape'][0],
            data['origin'][0]:data['origin'][0]+data['shape'][1],
        ]
        
        tracking = self.tracker.track(data['image'], background, None, T)
          
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
                
            if self.head_embedded:
                self.tracker = head_embedded_tracker(control, self.cam_fps)
            else:
                self.tracker = single_fish_tracker(control, self.cam_fps)
        
        # send tracking as metadata
        if self.current_tracking is None:
            return

        res = {}  
        res['tracker_metadata'] = self.current_tracking
        return res
        
