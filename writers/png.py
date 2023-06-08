from core.abstractclasses import ImageSaver
import cv2
from numpy.typing import NDArray
import os.path

class PNG_writer(ImageSaver):
    def __init__(
        self, 
        compression = 1,
        prefix: str= '',
        zeropad_n: int = 8
        ) -> None:

        super().__init__()
        if not 0 <= compression <= 9:
            ValueError('compression should be between 0 and 9')
        self._compression = compression
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
            [cv2.IMWRITE_PNG_COMPRESSION, self._compression]
        )
        self.img_num += 1