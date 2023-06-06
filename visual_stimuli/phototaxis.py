from numpy.typing import NDArray
import numpy as np
from core.dataclasses import TrackingCollection
from core.abstractclasses import Stimulus, Projector

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
                self.img = 1.0*(
                    ((self.grid_x-parameters.body.centroid[0]) * parameters.body.heading[0,1] + \
                    (self.grid_y-parameters.body.centroid[1]) * parameters.body.heading[1,1]) > 0
                )
            return self.img
        else:
            return None

    