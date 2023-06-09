from numpy.typing import NDArray
import numpy as np
from core.dataclasses import TrackingCollection
from core.abstractclasses import Stimulus, Projector
from numba import njit

@njit
def compute_image(xx,yy,centroid,heading):
    return 1.0*(((xx-centroid[0]) * heading[0,1] + (yy-centroid[1]) * heading[1,1]) > 0)

class Phototaxis(Stimulus):
    def __init__(self, projector: Projector):
        super().__init__()
        self.projector = projector
        self.last_timestamp = 0

        width, height = self.projector.get_resolution()
        xv, yv = np.meshgrid(range(width), range(height), indexing='xy')
        self.img = np.zeros((height,width), dtype=np.single)
        self.grid_x = xv
        self.grid_y = yv

    def create_stim_image(self, timestamp: int, parameters: TrackingCollection) -> NDArray:
        if timestamp > self.last_timestamp:
            self.last_timestamp = timestamp
            if parameters.body is not None:
                self.img = compute_image(self.grid_x,self.grid_y,parameters.body.centroid, parameters.body.heading)
            return self.img
        else:
            return None

    