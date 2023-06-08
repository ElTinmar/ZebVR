from writers.image_writer import ImageWriter
import cv2
from numpy.typing import NDArray

class JPG_writer(ImageWriter):
    def __init__(
            self, 
            quality: int = 95, 
            prefix: str = '',
            zeropad_n: int = 8
        ) -> None:

        super().__init__(prefix, zeropad_n)
        self._quality = quality
    
    def write(self, image: NDArray) -> None:
        # create filename and check it doesn't exist
        filename = self.create_filename('.jpg')
        
        # if image is type single, convert to uint8
        image_uint8 = self.to_uint8(image)

        # write image
        cv2.imwrite(
            filename,  
            image_uint8, 
            [cv2.IMWRITE_JPEG_QUALITY, self._quality]
        )
        self.img_num += 1
            