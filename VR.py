from typing import Protocol
from numpy.typing import NDArray
from dataclasses import dataclass

@dataclass
class EyeTracking:
    left_eye_angle: float
    right_eye_angle: float

@dataclass
class BodyTracking:
    centroid: NDArray
    heading: NDArray

@dataclass 
class TailTracking:
    tail_points: NDArray
    tail_angles: NDArray

@dataclass
class Tracking:
    body: BodyTracking
    eyes: EyeTracking
    tail: TailTracking

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

    def get_image() -> NDArray:
        """
        Output the next image from the camera
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

class VR:
    def __init__(
        self,
        camera: Camera, 
        projector: Projector,
        background: Background,
        cam2proj: Cam2Proj,
        tracker: Tracker,
        stimulus: Stimulus,
    ) -> None:
        
        self.camera = camera
        self.projector = projector
        self.background = background
        self.cam2proj = cam2proj
        self.tracker = tracker
        self.stimulus = stimulus

        self.calibration()
        self.registration()
        self.run()

    def calibration(self):
        self.camera.calibration()
        self.projector.calibration()

    def registration(self):
        self.cam2proj.registration()

    def run(self):
        while True:
            image = self.camera.get_image()
            self.background.add_image(image)
            background_image = self.background.get_background() 
            tracking = self.tracker.track(image-background_image)
            stim_image = self.stimulus.create_stim_image(tracking)
            self.projector.project(stim_image)

