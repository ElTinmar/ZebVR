from core.abstractclasses import ImageSaver
import cv2
from numpy.typing import NDArray
import os.path

class JPG_writer(ImageSaver):
    def __init__(
            self, 
            quality: int = 95, 
            prefix: str= '',
            zeropad_n: int = 8
        ) -> None:

        super().__init__()
        self._quality = quality
        self.prefix = prefix
        self.zeropad_n = zeropad_n
        self.img_num = 0
    
    def write(self, image: NDArray) -> None:
        filename = self.prefix + f'{self.img_num}'.zfill(self.zeropad_n) + '.jpg'
        if os.path.exists(filename):
            raise(FileExistsError)
        
        cv2.imwrite(
            filename,  
            image, 
            [cv2.IMWRITE_JPEG_QUALITY, self._quality]
        )
        self.img_num += 1
            