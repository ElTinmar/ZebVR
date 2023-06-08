from core.abstractclasses import ImageSaver
from numpy.typing import NDArray
import os.path
import numpy as np

class ImageWriter(ImageSaver):
    def __init__(
            self, 
            prefix: str = '',
            zeropad_n: int = 8
        ) -> None:

        super().__init__()
        self.prefix = prefix
        self.zeropad_n = zeropad_n
        self.img_num = 0

    def to_uint8(self, image: NDArray) -> NDArray:
        if image.dtype == np.uint8:
            return image
        else:
            rescaled = 255 * (image - image.min())/(image.max() - image.min())
            return rescaled.astype(np.uint8)
        
    def create_filename(self, extension: str) -> str:
        # create filename and check it doesn't exist
        filename = os.path.join(self.prefix, f'{self.img_num}'.zfill(self.zeropad_n) + extension)
        if os.path.exists(filename):
            raise(FileExistsError)
        return filename
    
    def write(self, image: NDArray) -> None:
        pass
            