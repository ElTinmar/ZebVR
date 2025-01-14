from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Any, Callable
import numpy as np
import cv2

def resize_to_closest_power_of_two(image: NDArray) -> NDArray:
    # some video_codecs require images with even size
    height, width = image.shape
    new_height = 2*(height//2) 
    new_width = 2*(width//2)
    image_resized = cv2.resize(
        image, 
        (new_width, new_height), 
        interpolation = cv2.INTER_NEAREST
    )
    return image_resized

class ImageFilterWorker(WorkerNode):

    def __init__(
        self, 
        image_function: Callable[[NDArray], NDArray],
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