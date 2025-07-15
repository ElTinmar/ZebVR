from dagline import WorkerNode
from typing import Any, List, Tuple
import numpy as np
from image_tools import im2gray, im2single

class CropWorker(WorkerNode):

    def __init__(
            self, 
            ROI_identities: List[Tuple[int,int,int,int]],
            *args, 
            **kwargs
        ):
        
        super().__init__(*args, **kwargs)
        self.ROI_identities = ROI_identities

    def process_data(self, data):
        
        if data is None:
            return
        
        res = {}
        for n, roi in enumerate(self.ROI_identities):
            x,y,w,h = roi
            crop = im2single(im2gray(data['image'][y:y+h,x:x+w])) 
            origin = np.array((x,y), dtype = np.int32)
            shape = np.array((h,w), dtype = np.int32) 
            res[f'cropper_output_{n}'] = np.array(
                (data['index'], data['timestamp'], crop, origin, shape, n),
                dtype=([
                    ('index', int),
                    ('timestamp', np.int64),
                    ('image', crop.dtype, crop.shape),
                    ('origin', np.int32, (2,)),
                    ('shape', np.int32, (2,)),
                    ('identity', np.int32)
                ])
            )            
        
        return res

    def process_metadata(self, metadata) -> Any:
        pass