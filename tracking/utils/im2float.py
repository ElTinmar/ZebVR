from numpy.typing import NDArray
import numpy as np

def im2single(input_image: NDArray) -> NDArray:
    """
    Transform input image into a single precision floating point image
    """
    ui_info = np.iinfo(input_image.dtype)
    return input_image.astype(np.float32) / ui_info.max
    
def im2double(input_image: NDArray) -> NDArray:
    """
    Transform input image into a double precision floating point image
    """
    ui_info = np.iinfo(input_image.dtype)
    return input_image.astype(np.float64) / ui_info.max

