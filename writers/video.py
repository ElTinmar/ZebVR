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
        if image.dtype == np.uint8:
            return image
        else:
            rescaled = 255 * (image - image.min())/(image.max() - image.min())
            return rescaled.astype(np.uint8)
            
    def to_BGR(self, image: NDArray) -> NDArray:
        if len(image.shape) == 2:
            return np.dstack((image,image,image))
        elif len(image.shape) == 3:
            return image
        else:
            raise(TypeError('Image shape not correct'))
        
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

    
