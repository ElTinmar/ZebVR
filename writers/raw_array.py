from writers.image_writer import ImageWriter
from numpy.typing import NDArray

class RawArray_writer(ImageWriter):
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

        super().__init__(prefix, zeropad_n)

    def write(self, image: NDArray) -> None:
        # create filename and check it doesn't exist
        filename = self.create_filename('.nparray')
        
        # if image is type single, convert to uint8
        image_uint8 = self.to_uint8(image)

        image_uint8.tofile(filename)
        self.img_num += 1