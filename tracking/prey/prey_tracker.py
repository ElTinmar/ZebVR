import numpy as np
from numpy.typing import NDArray
from tracking.utils.conncomp_filter import bwareafilter
from skimage.measure import label, regionprops
from core.abstractclasses import Tracker
import cv2
from core.dataclasses import PreyTracking

# TODO: track only at 10 Hz and predict the rest of
# the time
# Use hungarian assignment / kalman filters

class PreyTracker(Tracker):
    def __init__(
        self,
        threshold_prey_intensity: float,
        pixels_per_mm: float,
        threshold_prey_area_min_mm2: float = 0.3,
        threshold_prey_area_max_mm2: float = 2,
        rescale: float = None
    ) -> None:
        
        super().__init__()
        self.threshold_prey_intensity = threshold_prey_intensity
        self.threshold_prey_area_min_pix = threshold_prey_area_min_mm2 * pixels_per_mm
        self.threshold_prey_area_max_pix = threshold_prey_area_max_mm2 * pixels_per_mm
        self.rescale = rescale

        if rescale is not None:
            self.threshold_prey_area_min_pix *= rescale**2
            self.threshold_prey_area_max_pix *= rescale**2

    def track(self, image: NDArray) -> PreyTracking:
        
        # tracking is faster on small images
        if self.rescale is not None:
            image = cv2.resize(
                    image, 
                    None, 
                    fx = self.rescale, 
                    fy = self.rescale,
                    interpolation=cv2.INTER_NEAREST
                )
            
        prey_mask = bwareafilter(
            image >= self.threshold_prey_intensity, 
            min_size = self.threshold_prey_area_min_pix, 
            max_size = self.threshold_prey_area_max_pix
        )

        label_img = label(prey_mask)
        regions = regionprops(label_img)

        prey_centroids = np.empty((len(regions),2),dtype=np.float32)
        for i, blob in enumerate(regions):
            y, x = blob.centroid
            prey_centroids[i,:] = [x, y] 

        # scale back coordinates
        if self.rescale is not None:
            prey_centroids *= 1/self.rescale

        tracking = PreyTracking(
            prey_centroids = prey_centroids,
            prey_mask = prey_mask,
            image = image
        )

        return tracking
    