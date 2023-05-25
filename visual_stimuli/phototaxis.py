from typing import List
from numpy.typing import NDArray
from core.protocols import Projector
import numpy as np

class Phototaxis:
    def __init__(self, projector: Projector):
        
        self.projector = projector

    def create_stim_image(self, parameters: List[NDArray]) -> NDArray:
        width, height = self.projector.get_resolution()
        return np.ones((height,width))

    