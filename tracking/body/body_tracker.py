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
            pixels_per_mm: float,
            threshold_body_area_mm2: float = 10,
            dynamic_cropping_len_mm: float = 5,
            rescale: float = None
        ) -> None:

        super().__init__()
        self.threshold_body_intensity = threshold_body_intensity
        self.previous_centroid = None
        self.pixels_per_mm = pixels_per_mm
        self.rescale = rescale
        self.threshold_body_area_pix2 = threshold_body_area_mm2 * pixels_per_mm
        self.dynamic_cropping_len_pix = np.ceil(dynamic_cropping_len_mm * pixels_per_mm)

        if rescale is not None:
            self.threshold_body_area_pix2 *= rescale**2

    def track_pca(self, image: NDArray) -> BodyTracking:

        # threshold and remove small objects 
        fish_mask = bwareaopen(
            image >= self.threshold_body_intensity, 
            min_size = self.threshold_body_area_pix2
        )
              
        blob_coordinates = np.argwhere(fish_mask) #  (row, col) coordinates

        if blob_coordinates.size == 0:
            return None
        else:
            # (row,col) to (x,y) coordinates
            blob_coordinates = blob_coordinates[:,[1, 0]].astype('float')

            # scale back coordinates
            if self.rescale is not None:
                blob_coordinates *= 1/self.rescale

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
            tracking = BodyTracking(
                centroid = centroid,
                heading = principal_components,
                fish_mask = fish_mask
            )

            return tracking 
        
    def track(self, image: NDArray) -> BodyTracking:

        if self.previous_centroid is not None:
            left = max(self.previous_centroid[0] - self.dynamic_cropping_len_pix, 0)
            right = min(self.previous_centroid[0] + self.dynamic_cropping_len_pix, image.shape[1])
            bottom = max(self.previous_centroid[1] - self.dynamic_cropping_len_pix, 0)
            top = min(self.previous_centroid[1] + self.dynamic_cropping_len_pix, image.shape[0])
            imagecropped = image[left:right,bottom:top]

            # tracking is faster on small images
            if self.rescale is not None:
                imagecropped = cv2.resize(
                        imagecropped, 
                        None, 
                        fx = self.rescale, 
                        fy = self.rescale,
                        interpolation=cv2.INTER_NEAREST
                    )
       
            tracking = self.track_pca(imagecropped)
            if tracking is None:
                return self.track_pca(image)
            else:
                tracking.centroid += [left, bottom]
                self.previous_centroid = tracking.centroid
                return tracking
        else:
            # tracking is faster on small images
            if self.rescale is not None:
                image = cv2.resize(
                        image, 
                        None, 
                        fx = self.rescale, 
                        fy = self.rescale,
                        interpolation=cv2.INTER_NEAREST
                    )
                
            return self.track_pca(image)   
