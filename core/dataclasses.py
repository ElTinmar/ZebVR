from numpy.typing import NDArray
from dataclasses import dataclass
from typing import Tuple 

@dataclass
class Rect:
    left: int
    bottom: int
    width: int
    height: int
    
@dataclass
class CameraParameters:
    camera_index: int = 0, 
    exposure_time_ms: int = 10, 
    gain: int = 1, 
    ROI_top: int = 0, 
    ROI_left: int = 0, 
    ROI_height: int = 512, 
    ROI_width: int = 512, 
    triggers: bool = False, 
    fps: int = 100,

class Tracking:
    """
    This is an empty class to create a type for
    tracking results
    """

@dataclass
class BodyTracking(Tracking):
    centroid: NDArray
    centroid_small: NDArray
    heading: NDArray
    fish_mask: NDArray
    image: NDArray

@dataclass
class EyeParam:
    direction: NDArray
    angle: float
    centroid: NDArray 

@dataclass
class EyeTracking(Tracking):
    left_eye: EyeParam
    right_eye: EyeParam
    eye_mask: NDArray
    image: NDArray

@dataclass 
class TailTracking(Tracking):
    tail_points: NDArray
    tail_points_interp: NDArray
    origin: Tuple
    image: NDArray

@dataclass
class PreyTracking(Tracking):
    prey_centroids: NDArray
    prey_mask: NDArray
    image: NDArray

@dataclass
class TrackingCollection(Tracking):
    body: BodyTracking = None
    eyes: EyeTracking = None
    tail: TailTracking = None
    prey: PreyTracking = None

