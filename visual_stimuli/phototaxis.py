from typing import List
from numpy.typing import NDArray
from core.protocols import Projector
import numpy as np
from core.dataclasses import TrackingCollection
from core.abstractclasses import Stimulus

class Phototaxis(Stimulus):
    def __init__(self, projector: Projector):
        super().__init__()
        self.projector = projector

    def create_stim_image(self, parameters: TrackingCollection) -> NDArray:
        width, height = self.projector.get_resolution()
        xv, yv = np.meshgrid(range(width), range(height), indexing='xy')
        img = np.zeros((height,width), dtype=np.single)
        if parameters.body is not None:
            img = 1.0*(
                (xv * parameters.body.heading[0,1] - parameters.body.centroid[0] + \
                 yv * parameters.body.heading[1,1] - parameters.body.centroid[1]) > 0
            )
        return img

    