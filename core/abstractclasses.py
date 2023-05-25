from abc import ABC, abstractmethod
from numpy.typing import NDArray
from typing import Tuple
import logging
import cv2
import numpy as np
from screeninfo import get_monitors

class CameraData(ABC):
    """
    Adapter class to provide camera image and timestamps
    with a unified interface accross vendors.
    Also provides the queue method to reallocate image buffers
    to the camera
    """

    @abstractmethod
    def get_img(self) -> NDArray:
        """return image data"""
    
    @abstractmethod
    def get_timestamp(self) -> int:
        """return timestamps in ns"""

    @abstractmethod
    def reallocate(self):
        """return buffer to camera"""

class Camera(ABC):
    def __init__(
            self,
            camera_index = 0,
            exposure_time_ms = 10,
            gain = 4,
            ROI_top = 0,
            ROI_left = 0,
            ROI_height = 512,
            ROI_width = 512,
            triggers = False,
            fps = 100
    ) -> None:
        super().__init__()

        self.camera_index = camera_index
        self.exposure_time_ms = exposure_time_ms
        self.gain = gain
        self.ROI_top = ROI_top
        self.ROI_left = ROI_left
        self.ROI_height = ROI_height
        self.ROI_width = ROI_width
        self.triggers = triggers
        self.fps = fps

        self.logger = logging.getLogger('Camera')

    def start_acquisition() -> None:
        pass

    def stop_acquisition() -> None:
        pass

    def calibration() -> None:
        """
        Take picture of a checkerboard pattern with known world dimensions,
        correct image distortions and get mm/px.
        (Opt. correct for spatial intensity inhomogeneities: either fit a model
        with a few parameters e.g. a gaussian, or without a model with one 
        parameter for each pixel.)
        """
        ...

    def fetch() -> Tuple[CameraData, bool]:
        """
        Output a boolean if there is an image, 
        and the next image from the camera
        """
        ...

class Projector:

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
        cv2.waitKey(0)

        # TODO do the actual calibration

    def project(self, image: NDArray) -> None:
        """
        Input image to project
        """
        cv2.imshow('projector', image)
        cv2.waitKey(0)

    def __del__(self):
        cv2.destroyAllWindows()

from collections import deque
from scipy import stats

class Background:
    def __init__(self, num_images = 500, every_n_image = 100) -> None:
        self.num_images = num_images
        self.every_n_image = every_n_image
        self.image_store = deque(maxlen=num_images)
        self.counter = 0
        
    def add_image(self, image : NDArray) -> None:
        """
        Input an image to update the background model
        """
        self.counter += 1
        if self.counter % self.every_n_image == 0:
            self.image_store.append(image)

    def get_background(self) -> NDArray:
        """
        Outputs a background image
        """
        return stats.mode(self.image_store, axis=2, keepdims=False).mode