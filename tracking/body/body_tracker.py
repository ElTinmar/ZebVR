from typing import List 
import numpy as np
from numpy.typing import NDArray
from sklearn.decomposition import PCA
from tracking.utils.conncomp_filter import bwareaopen
from core.abstractclasses import Tracker
import cv2

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
        self.centroid = None
        self.principal_components = None
        self.fish_mask = None

        self.alpha = alpha
        self.color_heading = color_heading

    def track(self, image: NDArray) -> List[NDArray]:

        # threshold and remove small objects 
        fish_mask = bwareaopen(
            image >= self.threshold_body_intensity, 
            min_size = self.threshold_body_area
        )
        blob_coordinates = np.argwhere(fish_mask) #  (row, col) coordinates

        if blob_coordinates.size == 0:
            # nothing was detected above threshold
            self.centroid = None
            self.principal_components = None
            self.fish_mask = None

            return [None, None, None]
        else:
            # (row,col) to (x,y) coordinates
            blob_coordinates = blob_coordinates[:,[1, 0]]

            # PCA
            pca = PCA()
            scores = pca.fit_transform(blob_coordinates)
            # PCs are organized in rows, transform to columns
            principal_components = pca.components_.T
            centroid = pca.mean_

            # correct orientation
            if abs(max(scores[:,0])) > abs(min(scores[:,0])):
                principal_components[:,0] = - principal_components[:,0]
            if np.linalg.det(principal_components) < 0:
                principal_components[:,1] = - principal_components[:,1]

            # store to generate overlay
            self.centroid = centroid
            self.principal_components = principal_components
            self.fish_mask = fish_mask

            return [centroid, principal_components, fish_mask]
    
    def tracking_overlay(self, image: NDArray) -> NDArray:

        overlay = np.zeros(
            (image.shape[0],image.shape[1],3), 
            dtype=np.single
        )
        
        if self.fish_centroid is not None:
            pt1 = self.fish_centroid
            pt2 = self.fish_centroid + self.alpha*self.principal_components[:,0]
            overlay = cv2.line(
                overlay,
                pt1.astype(np.int32),
                pt2.astype(np.int32),
                self.color_heading
            )

        return overlay

        