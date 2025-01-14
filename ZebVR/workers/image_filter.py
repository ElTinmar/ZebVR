from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Any, Callable
import numpy as np

class ImageFilterWorker(WorkerNode):

    def __init__(
        self, 
        image_function: Callable,
        *args, 
        **kwargs
        ):
    
        super().__init__(*args, **kwargs)
        self.image_function = image_function

    def process_data(self, data: NDArray) -> None:
        if data is not None:
            image_processed = self.image_function(data['image']) 
            output = np.array(
                (data['index'], data['timestamp'], image_processed),
                dtype=np.dtype([
                    ('index', int),
                    ('timestamp', np.float64),
                    ('image', image_processed.dtype, image_processed.shape)
                ])
            )
            return output

    def process_metadata(self, metadata) -> Any:
        pass