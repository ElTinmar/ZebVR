from typing import List 
import numpy as np
from numpy.typing import NDArray
#from sklearnex import patch_sklearn
#patch_sklearn()
from sklearn.decomposition import PCA
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
            dynamic_cropping_len: int,
            height: int,
            width: int
        ) -> None:

        super().__init__()
        self.threshold_body_intensity = threshold_body_intensity
        self.threshold_body_area = threshold_body_area
        self.previous_centroid = None
        self.dynamic_cropping_len = dynamic_cropping_len
        self.height = height
        self.width = width

    def track(self):
        pass
    
class BodyTrackerPCA(BodyTracker):

    def track_pca(self, image: NDArray) -> BodyTracking:

        # threshold and remove small objects 
        fish_mask = bwareaopen(
            image >= self.threshold_body_intensity, 
            min_size = self.threshold_body_area
        )
        #print(f'bwareaopen {1e-9 *(time.process_time_ns() - start_time_ns)}')
              
        blob_coordinates = np.argwhere(fish_mask) #  (row, col) coordinates
        #print(f'argwhere {1e-9 *(time.process_time_ns() - start_time_ns)}')

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

            #print(f'PCA {1e-9 *(time.process_time_ns() - start_time_ns)}')

            # correct orientation
            if abs(max(scores[:,0])) > abs(min(scores[:,0])):
                principal_components[:,0] = - principal_components[:,0]
            if np.linalg.det(principal_components) < 0:
                principal_components[:,1] = - principal_components[:,1]

            # store to generate overlay
            tracking = BodyTracking(
                centroid = centroid,
                heading = principal_components,
                fish_mask = fish_mask
            )

            return tracking 
        
    def track(self, image: NDArray) -> BodyTracking:
        #start_time_ns = time.process_time_ns()

        if self.previous_centroid is not None:
            left = max(self.previous_centroid[0] - self.dynamic_cropping_len, 0)
            right = min(self.previous_centroid[0] + self.dynamic_cropping_len, self.width)
            bottom = max(self.previous_centroid[1] - self.dynamic_cropping_len, 0)
            top = min(self.previous_centroid[1] + self.dynamic_cropping_len, self.height)
            tracking = self.track_pca(image[left:right,bottom:top])
            if tracking is None:
                return self.track_pca(image)
            else:
                tracking.centroid += [left, bottom]
                self.previous_centroid = tracking.centroid
                return tracking
        else:
            return self.track_pca(image)   
