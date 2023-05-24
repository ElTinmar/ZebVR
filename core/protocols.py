from typing import Protocol, Tuple
from numpy.typing import NDArray
from .dataclasses import Tr

class Camera(Protocol):
    def calibration() -> None:
        """
        Take picture of a checkerboard pattern with known world dimensions,
        correct image distortions and get mm/px.
        (Opt. correct for spatial intensity inhomogeneities: either fit a model
        with a few parameters e.g. a gaussian, or without a model with one 
        parameter for each pixel.)
        """
        ...

    def get_image() -> Tuple[NDArray, bool]:
        """
        Output a boolean if there is an image, 
        and the next image from the camera
        """
        ...

class Background(Protocol):
    def add_image(NDArray) -> None:
        """
        Input an image to update the background model
        """
        ...

    def get_background() -> NDArray:
        """
        Outputs a background image
        """
        ...

class Projector(Protocol):
    def calibration() -> None:
        """
        Project a checkerboard on top of a real world checkerboard pattern 
        with known dimensions, correct image distortions and get mm/px.
        (Opt. correct for spatial intensity inhomogeneities: either fit a model
        with a few parameters e.g. a gaussian, or without a model with one 
        parameter for each pixel.)
        """
        ...

    def project(NDArray) -> None:
        """
        Input image to project
        """
        ...

class Cam2Proj(Protocol):
    def registration():
        """
        Project a grid of dots, one after the other on the screen,
        take a picture of each dot with the camera, and compute
        a linear (affine) map between projector and camera spaces
        """
        ...

    def transform_coordinates(NDArray) -> NDArray:
        """
        Input: camera coordinates
        Output: projector coordinates
        """
        ...

class Tracker(Protocol):
    def track(NDArray) -> Tracking:
        """
        Input: image from the camera,
        Output: position/orientation parameters
        """
        ...

class Stimulus(Protocol):
    def create_stim_image(Tracking) -> NDArray:
        """
        Input: fish position/orientation parameters from the Tracker,
        Output: corresponding stimulus image
        """
        ...