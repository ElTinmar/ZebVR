from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Any, Callable
import numpy as np
import cv2
from image_tools import rgb2gray, im2gray

def rgb_to_yuv420p(image_rgb: NDArray) -> NDArray:
    return cv2.cvtColor(image_rgb, cv2.COLOR_RGB2YUV_I420)

def gray_to_yuv420p(image_gray: NDArray) -> NDArray:
    image_rgb = np.dstack((image_gray, image_gray, image_gray))
    return rgb_to_yuv420p(image_rgb)

def rgb_to_gray(image_rgb: NDArray) -> NDArray:
    return im2gray(image_rgb)

def decimate(image: NDArray, k:int) -> NDArray:
    return image[::k,::k]

def bin(image: NDArray, k:int) -> NDArray:
    h, w = image.shape[:2]
    new_h, new_w = h // k, w // k  
    binned = image[:new_h * k, :new_w * k].reshape(new_h, k, new_w, k, -1).mean(axis=(1, 3))
    if binned.shape[-1] == 1:
        binned = binned.squeeze(-1)
    return binned

def resize_to_closest_multiple_of_two(image: NDArray, height: int, width: int) -> NDArray:
    # some video_codecs require images with even size
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