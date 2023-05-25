from abc import ABC, abstractmethod
from numpy.typing import NDArray
from typing import Tuple, List
import logging

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

    def get_resolution(self) -> Tuple[int,int]:
        return (self.ROI_width, self.ROI_height)

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
    
class Tracker(ABC):
    @abstractmethod
    def track(self, image: NDArray) -> List[NDArray]:
        """
        Extract parameters (position/orientation) 
        of objects from an image
        """