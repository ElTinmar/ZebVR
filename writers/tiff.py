from core.abstractclasses import ImageSaver
import cv2
from enum import Enum
from numpy.typing import NDArray
import os.path

class TiffCompression(Enum):
    COMPRESSION_NONE = 1
    COMPRESSION_LZW = 5
    COMPRESSION_ADOBE_DEFLATE = 8
    COMPRESSION_DEFLATE = 32946
    COMPRESSION_JP2000 = 34712

class TIFF_writer(ImageSaver):
    def __init__(
            self, 
            compression_type = TiffCompression.COMPRESSION_LZW,
            prefix: str= '',
            zeropad_n: int = 8
        ) -> None:

        super().__init__()
        if compression_type not in TiffCompression:
            ValueError('Use TiffCompression enum')
        self.compression_type = compression_type
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
            [cv2.IMWRITE_TIFF_COMPRESSION, self.compression_type]
        )
        self.img_num += 1