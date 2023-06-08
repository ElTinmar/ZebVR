from writers.image_writer import ImageWriter
import cv2
from enum import IntEnum
from numpy.typing import NDArray

class TiffCompression(IntEnum):
    COMPRESSION_NONE = 1
    COMPRESSION_LZW = 5
    COMPRESSION_ADOBE_DEFLATE = 8
    COMPRESSION_DEFLATE = 32946
    COMPRESSION_JP2000 = 34712

class TIFF_writer(ImageWriter):
    def __init__(
            self, 
            compression_type = TiffCompression.COMPRESSION_LZW,
            prefix: str = '',
            zeropad_n: int = 8
        ) -> None:

        super().__init__(prefix, zeropad_n)
        if compression_type not in TiffCompression:
            ValueError('Use TiffCompression enum')
        self.compression_type = compression_type
    
    def write(self, image: NDArray) -> None:
        # create filename and check it doesn't exist
        filename = self.create_filename('.tiff')
        
        # if image is type single, convert to uint8
        image_uint8 = self.to_uint8(image)

        cv2.imwrite(
            filename,  
            image_uint8, 
            [cv2.IMWRITE_TIFF_COMPRESSION, self.compression_type]
        )
        self.img_num += 1