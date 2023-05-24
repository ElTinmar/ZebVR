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
