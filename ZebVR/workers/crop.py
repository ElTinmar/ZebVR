from dagline import WorkerNode
from typing import Any, List, Tuple
import numpy as np

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

# EXPERIMENTAL: pre-allocate. Need to pass num channels
class CropWorker2(WorkerNode):

    def __init__(
            self, 
            ROI_identities: List[Tuple[int,int,int,int]],
            n_channels: int,
            *args, 
            **kwargs
        ):
        
        super().__init__(*args, **kwargs)
        self.ROI_identities = ROI_identities

        self.buffers = []
        for x, y, w, h in ROI_identities:
            dtype = np.dtype([
                ('index', int),
                ('timestamp', np.int64),
                ('image', np.uint8, (h, w, n_channels)), 
                ('origin', np.int32, (2,)),
                ('shape', np.int32, (2,)),
                ('identity', np.int32)
            ])
            # Pre-allocate memory once
            self.buffers.append(np.zeros((), dtype=dtype))

    def process_data(self, data):
        
        if data is None:
            return
        
        res = {}
        for n, (roi, buf) in enumerate(zip(self.ROI_identities, self.buffers)):
            x,y,w,h = roi
            buf['index'] = data['index']
            buf['timestamp'] = data['timestamp']
            buf['image'][:] = data['image'][y:y+h, x:x+w]
            buf['origin'] = (x, y)
            buf['shape'] = (h, w)
            buf['identity'] = n
            res[f'cropper_output_{n}'] = buf          
        
        return res

    def process_metadata(self, metadata) -> Any:
        pass