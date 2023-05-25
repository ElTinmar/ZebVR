from screeninfo import get_monitors
from numpy.typing import NDArray
import cv2
import numpy as np
from typing import Tuple

class CVProjector:
    def __init__(self, monitor_id=1) -> None:

        offset_x = 0
        for id, monitor in enumerate(get_monitors()):
            width = monitor.width
            height = monitor.height
            if id == monitor_id:
                break
            offset_x = offset_x + width

        cv2.namedWindow('projector',  cv2.WINDOW_NORMAL)
        cv2.moveWindow('projector', x=offset_x, y=0)
        cv2.resizeWindow('projector', width, height)

        self.monitor_id = monitor_id
        self.win_width = width
        self.win_height = height

    def calibration(self, num_pixels = 100) -> None:
        """
        Project a checkerboard on top of a real world checkerboard pattern 
        with known dimensions, correct image distortions and get mm/px.
        (Opt. correct for spatial intensity inhomogeneities: either fit a model
        with a few parameters e.g. a gaussian, or without a model with one 
        parameter for each pixel.)
        """

        xv, yv = np.meshgrid(range(self.win_width), range(self.win_height), indexing='xy')
        checkerboard = ((xv // num_pixels) + (yv // num_pixels)) % 2
        checkerboard = 255*checkerboard.astype(np.uint8)
        cv2.imshow('projector', checkerboard)
        cv2.waitKey(1)

        # TODO do the actual calibration

    def project(self, image: NDArray) -> None:
        """
        Input image to project
        """
        cv2.imshow('projector', image)
        cv2.waitKey(1)

    def get_resolution(self) -> Tuple[int, int]:
        return (self.win_width, self.win_height)

    def __del__(self):
        cv2.destroyWindow('projector')