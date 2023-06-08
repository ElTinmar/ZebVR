from core.abstractclasses import ImageSaver
import os.path
from numpy.typing import NDArray

class RawArray_writer(ImageSaver):
    """
    Definitely faster than using cv2.imwrite with JPG2000 compression
    but generates large annoying files.
    For 1024x1024 @ 200Hz it's around 1TB per hour  
    """
    def __init__(
        self,
        prefix: str= '',
        zeropad_n: int = 8
        ) -> None:

        super().__init__()
        self.prefix = prefix
        self.zeropad_n = zeropad_n
        self.img_num = 0

    def write(self, image: NDArray) -> None:
        filename = self.prefix + f'{self.img_num}'.zfill(self.zeropad_n) + '.jpg'
        if os.path.exists(filename):
            raise(FileExistsError)
        image.tofile(filename + '.nparray')
        self.img_num += 1