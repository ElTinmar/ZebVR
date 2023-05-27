from numpy.typing import NDArray
from abc import ABC, abstractmethod
from dataclasses import dataclass

# https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html

class GeometricDistortion(ABC):
    pass

class IntensityDistortion(ABC):
    pass

@dataclass
class GaussianIntensity(IntensityDistortion):
    mu: NDArray
    sigma: NDArray

@dataclass
class LinearIntensity(IntensityDistortion):
    pass

@dataclass
class BarrelPincushionParam(GeometricDistortion):
    # https://en.wikipedia.org/wiki/Distortion_(optics)
    K: NDArray
    P: NDArray
    C: NDArray

@dataclass
class CylindricalParam(GeometricDistortion):
    # https://en.wikipedia.org/wiki/Central_cylindrical_projection
    R: float
    lambda_0: float
    x_0: int
    y_0: int
    scale_x: float
    scale_y: float

@dataclass
class ShpericalParam(GeometricDistortion):
    pass

@dataclass
class AffineParam(GeometricDistortion):
    T: NDArray

class Correction(ABC):
    def __init__(
            self, 
            geometric_param: GeometricDistortion,
            intensity_param: IntensityDistortion
        )-> None:
        
        self.geometric_param = geometric_param
        self.intensity_param = intensity_param

    @abstractmethod
    def transform(self, image: NDArray) -> NDArray:
        pass

class BarrelPincushionCorrection(Correction):
    def transform(self, image: NDArray) -> NDArray:
        pass    

class AffineCorrection(Correction):
    def transform(self, image: NDArray) -> NDArray:
        pass

class CylinderCorrection(Correction):
    def transform(self, image: NDArray) -> NDArray:
        pass
    
class SphericalCorrection(Correction):
    def transform(self, image: NDArray) -> NDArray:
        pass