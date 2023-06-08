from core.abstractclasses import ImageSaver
import cv2
from numpy.typing import NDArray
import os.path
import numpy as np

class CVWriter(ImageSaver):
    def __init__(
            self, 
            height: int, 
            width: int, 
            fps: int = 30, 
            filename: str = '',
            codec: str = 'MJPG'
        ) -> None:
        super().__init__()
        
        if os.path.exists(filename):
            raise(FileExistsError)
        
        self.fps = fps
        self.filename = filename
        self.height = height
        self.width = width
        self.codec = codec
    
    def to_uint8(self, image: NDArray) -> NDArray:
        if image.dtype is not np.uint8:
            rescaled = 255 * (image - image.min())/(image.max() - image.min())
            return rescaled.astype(np.uint8)
        else:
            return image
        
    def to_BGR(self, image_gray: NDArray) -> NDArray:
        return np.dstack((image_gray,image_gray,image_gray))
        
    def start(self) -> None: 
        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        self.cap = cv2.VideoWriter(
            self.filename,
            fourcc,
            self.fps,
            (self.width,self.height)
        )

    def stop(self) -> None:
        self.cap.release()

    def write(self, image: NDArray) -> None:
        image_uint8 = self.to_uint8(image)
        image_BGR_uint8 = self.to_BGR(image_uint8)
        self.cap.write(image_BGR_uint8)

    
