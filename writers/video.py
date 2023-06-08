from core.abstractclasses import ImageSaver
import cv2
from numpy.typing import NDArray
import os.path

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
        self.cap.write(image)

    
