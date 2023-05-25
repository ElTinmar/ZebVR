from typing import List 
import numpy as np
from numpy.typing import NDArray
from tracking.utils.conncomp_filter import bwareafilter
from skimage.measure import label, regionprops
from core.abstractclasses import Tracker
import cv2

class PreyTracker(Tracker):
    def __init__(
        self,
        threshold_prey_intensity: float,
        threshold_prey_area_min: int,
        threshold_prey_area_max: int,
        circle_radius: int = 10, 
        circle_color: tuple = (0,1,0)
    ) -> None:
        
        super().__init__()
        self.threshold_prey_intensity = threshold_prey_intensity
        self.threshold_prey_area_min = threshold_prey_area_min  
        self.threshold_prey_area_max = threshold_prey_area_max 
        self.prey_centroids = None
        self.prey_mask = None

        # overlay parameters
        self.circle_radius = circle_radius
        self.circle_color = circle_color

    def track(self, image: NDArray) -> List[NDArray]:

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

        self.prey_centroids = prey_centroids
        self.prey_mask = prey_mask

        return [prey_centroids, prey_mask]
    
    def tracking_overlay(self, image: NDArray) -> NDArray:

        overlay = np.zeros(
            (image.shape[0],image.shape[1],3), 
            dtype=np.single
        )

        for prey_loc in self.prey_centroids:
            overlay = cv2.circle(
                overlay, 
                prey_loc.astype(np.int32),
                self.circle_radius,
                self.circle_color
            )

        return overlay