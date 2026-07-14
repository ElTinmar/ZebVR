from dagline import WorkerNode
from typing import Any, Dict
import numpy as np

class CropWorker(WorkerNode):

    def __init__(
            self, 
            identities: Dict,
            *args, 
            **kwargs
        ):
        
        super().__init__(*args, **kwargs)
        self.identities = identities

    def process_data(self, data):
        
        if data is None:
            return
        
        res = {}
        for n, coordinates in self.identities.items():
            x,y,w,h = coordinates['bbox_rect']
            crop = data['image'][y:y+h,x:x+w]
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
