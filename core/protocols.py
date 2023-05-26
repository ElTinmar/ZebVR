from typing import Protocol, Tuple, List
from numpy.typing import NDArray
from .abstractclasses import CameraData
from .dataclasses import Tracking, TrackingCollection

class Camera(Protocol):
    def start_acquisition(self) -> None:
        ...

    def stop_acquisition(self) -> None:
        ...

    def calibration(self) -> None:
        """
        Take picture of a checkerboard pattern with known world dimensions,
        correct image distortions and get mm/px.
        (Opt. correct for spatial intensity inhomogeneities: either fit a model
        with a few parameters e.g. a gaussian, or without a model with one 
        parameter for each pixel.)
        """
        ...

    def fetch(self) -> Tuple[CameraData, bool]:
        """
        Output a boolean if there is an image, 
        and the next image from the camera
        """
        ...

    def get_resolution(self) -> Tuple[int, int]:
        """
        Get resolution
        """
        
class Background(Protocol):
    def add_image(self, image: NDArray) -> None:
        """
        Input an image to update the background model
        """
        ...

    def get_background(self) -> NDArray:
        """
        Outputs a background image
        """
        ...

class Projector(Protocol):
    def calibration(self) -> None:
        """
        Project a checkerboard on top of a real world checkerboard pattern 
        with known dimensions, correct image distortions and get mm/px.
        (Opt. correct for spatial intensity inhomogeneities: either fit a model
        with a few parameters e.g. a gaussian, or without a model with one 
        parameter for each pixel.)
        """
        ...

    def project(self, image: NDArray) -> None:
        """
        Input image to project
        """
        ...

    def get_resolution(self) -> Tuple[int, int]:
        """
        Get resolution
        """

class Cam2Proj(Protocol):
    def registration(self):
        """
        Project a grid of dots, one after the other on the screen,
        take a picture of each dot with the camera, and compute
        a linear (affine) map between projector and camera spaces
        """
        ...

    def transform_coordinates(self, coord: NDArray) -> NDArray:
        """
        Input: camera coordinates
        Output: projector coordinates
        """
        ...

class Tracker(Protocol):
    def track(self, image: NDArray) -> Tracking:
        """
        Input: image from the camera,
        Output: position/orientation parameters
        """
        ...

    def tracking_overlay(self, image: NDArray) -> NDArray:
        """
        Return overlay image to visualize tracking parameters
        """
        ...

class Stimulus(Protocol):
    def create_stim_image(self, parameters: TrackingCollection) -> NDArray:
        """
        Input: fish position/orientation parameters from the Tracker,
        Output: corresponding stimulus image
        """
        ...