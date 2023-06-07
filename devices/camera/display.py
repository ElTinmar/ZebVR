from numpy.typing import NDArray
from core.abstractclasses import CameraDisplay
import cv2

class CamDisp(CameraDisplay):
    def __init__(self, name: str, rescale: float = None) -> None:
        super().__init__()
        self.name = name
        self.rescale = rescale

    def init_window(self):
        cv2.namedWindow(self.name)

    def close_window(self):
        cv2.destroyWindow(self.name)

    def display(self, image: NDArray) -> None:
        if self.rescale is not None:
            smallimg = cv2.resize(
                image, 
                None, 
                fx = self.rescale, 
                fy = self.rescale, 
                interpolation=cv2.INTER_NEAREST
            )
            cv2.imshow(self.name, smallimg)
        else:
            cv2.imshow(self.name, image)
        cv2.waitKey(1)