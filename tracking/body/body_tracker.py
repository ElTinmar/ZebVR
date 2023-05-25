from typing import List 
import numpy as np
from numpy.typing import NDArray
from sklearn.decomposition import PCA
from utils.conncomp_filter import bwareaopen
from core.abstractclasses import Tracker

class BodyTracker(Tracker):
    def __init__(
            self, 
            threshold_body_intensity: float, 
            threshold_body_area: int
        ) -> None:

        super().__init__()
        self.threshold_body_intensity = threshold_body_intensity
        self.threshold_body_area = threshold_body_area

    def track(self, image: NDArray) -> List[NDArray]:

        # threshold and remove small objects 
        fish_mask = bwareaopen(
            image >= self.threshold_body_intensity, 
            min_size = self.threshold_body_area
        )
        blob_coordinates = np.argwhere(fish_mask) #  (row, col) coordinates

        if blob_coordinates.size == 0:
            # nothing was detected above threshold
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

            return [centroid, principal_components, fish_mask]
        