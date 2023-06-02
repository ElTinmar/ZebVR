from typing import List 
import numpy as np
from numpy.typing import NDArray
#from sklearnex import patch_sklearn
#patch_sklearn()
from sklearn.decomposition import PCA
from skimage.measure import moments_central
from tracking.utils.conncomp_filter import bwareaopen
from core.abstractclasses import Tracker
import cv2
from core.dataclasses import BodyTracking
import time

class BodyTracker(Tracker):
    def __init__(
            self, 
            threshold_body_intensity: float, 
            threshold_body_area: int,
            alpha: int = 100,
            color_heading: tuple = (0,0,1)
        ) -> None:

        super().__init__()
        self.threshold_body_intensity = threshold_body_intensity
        self.threshold_body_area = threshold_body_area

        self.curr_tracking = None

        self.alpha = alpha
        self.color_heading = color_heading

    def track(self):
        pass
    
    def tracking_overlay(self, image: NDArray) -> NDArray:

        overlay = np.zeros(
            (image.shape[0],image.shape[1],3), 
            dtype=np.single
        )
        
        if self.curr_tracking is not None:
            pt1 = self.curr_tracking.centroid
            pt2 = self.curr_tracking.centroid + self.alpha*self.curr_tracking.heading[:,0]
            overlay = cv2.line(
                overlay,
                pt1.astype(np.int32),
                pt2.astype(np.int32),
                self.color_heading
            )

        return overlay
    
class BodyTrackerPCA(BodyTracker):
    def track(self, image: NDArray) -> BodyTracking:
        #start_time_ns = time.process_time_ns()

        # threshold and remove small objects 
        fish_mask = bwareaopen(
            image >= self.threshold_body_intensity, 
            min_size = self.threshold_body_area
        )
        #print(f'bwareaopen {10e-9 *(time.process_time_ns() - start_time_ns)}')
              
        blob_coordinates = np.argwhere(fish_mask) #  (row, col) coordinates
        #print(f'argwhere {10e-9 *(time.process_time_ns() - start_time_ns)}')

        if blob_coordinates.size == 0:
            return None
        else:
            # (row,col) to (x,y) coordinates
            blob_coordinates = blob_coordinates[:,[1, 0]]

            # PCA
            pca = PCA()
            scores = pca.fit_transform(blob_coordinates)
            # PCs are organized in rows, transform to columns
            principal_components = pca.components_.T
            centroid = pca.mean_

            #print(f'PCA {10e-9 *(time.process_time_ns() - start_time_ns)}')

            # correct orientation
            if abs(max(scores[:,0])) > abs(min(scores[:,0])):
                principal_components[:,0] = - principal_components[:,0]
            if np.linalg.det(principal_components) < 0:
                principal_components[:,1] = - principal_components[:,1]

            # store to generate overlay
            self.curr_tracking = BodyTracking(
                centroid = centroid,
                heading = principal_components,
                fish_mask = fish_mask
            )

            return self.curr_tracking 

class BodyTrackerMoments(BodyTracker):
    def track(self, image: NDArray) -> BodyTracking:

        # threshold and remove small objects 
        fish_mask = bwareaopen(
            image >= self.threshold_body_intensity, 
            min_size = self.threshold_body_area
        )

        # TODO 
        
        return None