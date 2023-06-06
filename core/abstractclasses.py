from abc import ABC, abstractmethod
from numpy.typing import NDArray
from typing import Tuple, List
import logging
from core.dataclasses import CameraParameters, Tracking

class CameraData(ABC):
    """
    Adapter class to provide camera image and timestamps
    with a unified interface accross vendors.
    Also provides the queue method to reallocate image buffers
    to the camera
    """

    def __init__(self, param: CameraParameters) -> None:
        super().__init__()
        self.parameters = param

    @abstractmethod
    def get_img(self) -> NDArray:
        """return image data"""
    
    @abstractmethod
    def get_index(self) -> int:
        """return frame index"""

    @abstractmethod
    def get_timestamp(self) -> int:
        """return timestamps in ns"""

    @abstractmethod
    def reallocate(self):
        """return buffer to camera"""

class Projector(ABC):
    @abstractmethod
    def calibration(self) -> None:
        """
        Project a checkerboard on top of a real world checkerboard pattern 
        with known dimensions, correct image distortions and get mm/px.
        (Opt. correct for spatial intensity inhomogeneities: either fit a model
        with a few parameters e.g. a gaussian, or without a model with one 
        parameter for each pixel.)
        """
        ...

    @abstractmethod
    def init_window(self) -> None:
        pass
    
    @abstractmethod
    def close_window(self) -> None:
        pass

    @abstractmethod
    def project(self, image: NDArray) -> None:
        """
        Input image to project
        """
        ...
    @abstractmethod
    def get_resolution(self) -> Tuple[int, int]:
        """
        Get resolution
        """

class Camera(ABC):
    def __init__(
            self,
            parameters: CameraParameters
    ) -> None:
        super().__init__()

        self.parameters = parameters
        self.logger = logging.getLogger('Camera')

    def start_acquisition(self) -> None:
        pass
    
    def stop_acquisition(self) -> None:
        pass

    def get_resolution(self) -> Tuple[int,int]:
        return (self.parameters.ROI_width, self.parameters.ROI_height)

    def calibration(self) -> None:
        """
        Take picture of a checkerboard pattern with known world dimensions,
        correct image distortions and get mm/px.
        (Opt. correct for spatial intensity inhomogeneities: either fit a model
        with a few parameters e.g. a gaussian, or without a model with one 
        parameter for each pixel.)
        """
        
    @abstractmethod
    def fetch(self) -> Tuple[CameraData, bool]:
        """
        Output a boolean if there is an image, 
        and the next image from the camera
        """

class CameraDisplay(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def init_window(self) -> None:
        pass

    @abstractmethod
    def close_window(self) -> None:
        pass

    @abstractmethod
    def display(self, image: NDArray) -> None:
        pass

class Tracker(ABC):
    def __init__(self):
        super().__init__()
            
    @abstractmethod
    def track(self, image: NDArray) -> List[NDArray]:
        """
        Extract parameters (position/orientation) 
        of objects from an image
        """
        
class TrackerDisplay(ABC):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def init_window(self):
        pass
    
    @abstractmethod
    def close_window(self):
        pass

    @abstractmethod
    def display(self, parameters: Tracking, image: NDArray) -> NDArray:
        pass

class Background(ABC):
    @abstractmethod
    def add_image(self, image : NDArray) -> None:
        """
        Add images to the background model
        """

    @abstractmethod
    def get_background(self) -> NDArray:
        """
        Return background model image
        """

class Stimulus(ABC):
     @abstractmethod
     def create_stim_image(self, parameters: Tracking) -> NDArray:
        """
        create stimulus image from tracking parameters
        """

class Cam2Proj(ABC):
    def registration(self):
        """
        Project a grid of dots, one after the other on the screen,
        take a picture of each dot with the camera, and compute
        a linear (affine) map between projector and camera spaces
        """

    def transform_coordinates(self, coord: NDArray) -> NDArray:
        """
        Input: camera coordinates
        Output: projector coordinates
        """