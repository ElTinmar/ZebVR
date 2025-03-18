from video_tools import BackgroundSubtractor
from dagline import WorkerNode
from typing import Any, List, Tuple
import numpy as np

class BackgroundSubWorker(WorkerNode):

    def __init__(
            self, 
            sub: BackgroundSubtractor, 
            ROI_identities: List[Tuple[int,int,int,int]],
            *args, 
            **kwargs
        ):
        
        super().__init__(*args, **kwargs)
        self.sub = sub
        self.ROI_identities = ROI_identities

    def initialize(self) -> None:
        super().initialize()
        self.sub.initialize()

    def process_data(self, data):

        if data is not None:

            background_sub = self.sub.subtract_background(data['image'])
            
            res = {}
            for n, roi in enumerate(self.ROI_identities):
                x,y,w,h = roi
                crop = background_sub[y:y+h,x:x+w]
                origin = np.array((x,y), dtype = np.int32)
                res[f'background_output_{n}'] = np.array(
                    (data['index'], data['timestamp'], crop, origin, n),
                    dtype=([
                        ('index', int),
                        ('timestamp', np.float64),
                        ('image', crop.dtype, crop.shape),
                        ('origin', np.int32, (2,)),
                        ('identity', np.int32)
                    ])
                )            
            
            return res

    def process_metadata(self, metadata) -> Any:
        pass