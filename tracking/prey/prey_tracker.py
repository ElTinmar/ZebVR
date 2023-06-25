import numpy as np
from numpy.typing import NDArray
from tracking.utils.conncomp_filter import bwareafilter_centroids
from core.abstractclasses import Tracker
import cv2
from core.dataclasses import PreyTracking
from collections import deque

# TODO: track only at 10 Hz and predict the rest of
# the time
# Use hungarian assignment / kalman filters

# Use connected components in 3D (x,y,t)

class PreyTracker(Tracker):
    def __init__(
        self,
        threshold_prey_intensity: float,
        pixels_per_mm: float,
        threshold_prey_area_min_mm2: float = 0.6,
        threshold_prey_area_max_mm2: float = 1.5,
        rescale: float = None
    ) -> None:
        
        super().__init__()
        self.threshold_prey_intensity = threshold_prey_intensity
        self.threshold_prey_area_min_pix = threshold_prey_area_min_mm2 * pixels_per_mm
        self.threshold_prey_area_max_pix = threshold_prey_area_max_mm2 * pixels_per_mm
        self.rescale = rescale

        self.last_masks = deque(maxlen=10)
        self.counter = 0
        self.results = None

        if rescale is not None:
            self.threshold_prey_area_min_pix *= rescale**2
            self.threshold_prey_area_max_pix *= rescale**2

    def track(self, image: NDArray) -> PreyTracking:
        
        if self.counter % 10 == 0:
            # tracking is faster on small images
            if self.rescale is not None:
                image = cv2.resize(
                        image, 
                        None, 
                        fx = self.rescale, 
                        fy = self.rescale,
                        interpolation=cv2.INTER_NEAREST
                    )
 
            prey_centroids = bwareafilter_centroids(
                image >= self.threshold_prey_intensity, 
                min_size = self.threshold_prey_area_min_pix, 
                max_size = self.threshold_prey_area_max_pix
            )

            # scale back coordinates
            if self.rescale is not None:
                prey_centroids *= 1/self.rescale

            tracking = PreyTracking(
                prey_centroids = prey_centroids,
                prey_mask = None,
                image = image
            )

            self.results = tracking

        self.counter += 1
        return self.results
    