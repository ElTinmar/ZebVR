from numpy.typing import NDArray
from core.abstractclasses import CameraDisplay
import cv2

class CamDisp(CameraDisplay):
    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name

    def init_window(self):
        cv2.namedWindow(self.name)

    def close_window(self):
        cv2.destroyWindow(self.name)

    def display(self, image: NDArray) -> None:
        cv2.imshow(self.name, image)
        cv2.waitKey(1)