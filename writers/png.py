from writers.image_writer import ImageWriter
import cv2
from numpy.typing import NDArray

class PNG_writer(ImageWriter):
    def __init__(
        self, 
        compression = 1,
        prefix: str= '',
        zeropad_n: int = 8
        ) -> None:

        super().__init__(prefix, zeropad_n)
        if not 0 <= compression <= 9:
            ValueError('compression should be between 0 and 9')
        self._compression = compression
    
    def write(self, image: NDArray) -> None:
        # create filename and check it doesn't exist
        filename = self.create_filename('.png')
        
        # if image is type single, convert to uint8
        image_uint8 = self.to_uint8(image)
        
        cv2.imwrite(
            filename,  
            image_uint8, 
            [cv2.IMWRITE_PNG_COMPRESSION, self._compression]
        )
        self.img_num += 1