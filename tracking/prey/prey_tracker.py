import numpy as np
from numpy.typing import NDArray
from tracking.utils.conncomp_filter import bwareafilter
from skimage.measure import label, regionprops
from core.abstractclasses import Tracker
import cv2
from core.dataclasses import PreyTracking

class PreyTracker(Tracker):
    def __init__(
        self,
        threshold_prey_intensity: float,
        threshold_prey_area_min: int,
        threshold_prey_area_max: int
    ) -> None:
        
        super().__init__()
        self.threshold_prey_intensity = threshold_prey_intensity
        self.threshold_prey_area_min = threshold_prey_area_min  
        self.threshold_prey_area_max = threshold_prey_area_max 

    def track(self, image: NDArray) -> PreyTracking:

        prey_mask = bwareafilter(
            image >= self.threshold_prey_intensity, 
            min_size = self.threshold_prey_area_min, 
            max_size = self.threshold_prey_area_max
        )

        label_img = label(prey_mask)
        regions = regionprops(label_img)

        prey_centroids = np.empty((len(regions),2),dtype=np.float32)
        for i,blob in enumerate(regions):
            prey_centroids[i,:] = [blob.centroid[1], blob.centroid[0]] 

        tracking = PreyTracking(
            prey_centroids = prey_centroids,
            prey_mask = prey_mask
        )

        return tracking
    