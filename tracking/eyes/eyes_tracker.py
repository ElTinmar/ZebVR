from typing import List 
import numpy as np
from numpy.typing import NDArray
from tracking.utils.conncomp_filter import bwareafilter
from skimage.measure import label, regionprops
from sklearn.decomposition import PCA
from core.abstractclasses import Tracker
from tracking.body.body_tracker import BodyTracker
from core.dataclasses import EyeTracking, EyeParam, Rect
import cv2
from tracking.utils.geometry import ellipse_direction, angle_between_vectors
from tracking.utils.diagonal_imcrop import diagonal_crop

class EyesTracker(Tracker):
    def __init__(
        self,
        pixels_per_mm: float,
        threshold_eye_intensity: float,
        dynamic_cropping_len_mm: float = 5,
        threshold_eye_area_min_mm2: float = 2,
        threshold_eye_area_max_mm2: float = 10,
        dist_eye_midline_mm: float = 0.1,
        dist_eye_swimbladder_mm: float = 0.2,
        rescale: float = None
    ) -> None:
        
        super().__init__()
        self.pixels_per_mm = pixels_per_mm
        self.threshold_eye_intensity = threshold_eye_intensity
        self.threshold_eye_area_min_pix2 = threshold_eye_area_min_mm2 * pixels_per_mm
        self.threshold_eye_area_max_pix2 = threshold_eye_area_max_mm2 * pixels_per_mm
        self.dist_eye_midline_pix = dist_eye_midline_mm * pixels_per_mm
        self.dist_eye_swimbladder_pix = dist_eye_swimbladder_mm * pixels_per_mm
        self.dynamic_cropping_len_pix = int(np.ceil(dynamic_cropping_len_mm * pixels_per_mm))
        self.rescale = rescale

        if rescale is not None:
            self.threshold_eye_area_min_pix2 *= rescale**2
            self.threshold_eye_area_max_pix2 *= rescale**2
            self.dist_eye_midline_pix *= rescale
            self.dist_eye_swimbladder_pix *= rescale
        
    @staticmethod
    def track_eye(
        image: NDArray,
        threshold_eye_intensity: float, 
        threshold_eye_area_min_pix2: float,
        threshold_eye_area_max_pix2: float
    ):
        
        eye_mask = bwareafilter(
            image >= threshold_eye_intensity, 
            min_size = threshold_eye_area_min_pix2, 
            max_size = threshold_eye_area_max_pix2
        )

        blob_coordinates = np.argwhere(eye_mask)

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

            # correct orientation
            if np.linalg.det(principal_components) < 0:
                principal_components[:,1] = - principal_components[:,1]
            
            angle = np.arctan2(
                -principal_components[1,0],
                principal_components[0,0]
            ) 

            # store to generate overlay
            result = EyeParam(
                centroid = centroid,
                direction = principal_components[:,0],
                angle = angle
            )

            return result

    def track(
            self, 
            image: NDArray, 
            centroid: NDArray, 
            heading: NDArray
        ) -> EyeTracking:

        angle = np.arctan2(heading[1,1],heading[0,1]) 
        corner = centroid - 30 * heading[:,1] + 40* heading[:,0]
        image_eyes = diagonal_crop(
            image, 
            Rect(corner[0],corner[1],60,40),
            np.rad2deg(angle)
        )
        '''
        cv2.namedWindow('eyes')
        cv2.imshow('eyes',image_eyes)
        cv2.waitKey(1)   
        '''
        tracking = EyeTracking(
            left_eye = EyesTracker.track_eye(
                image_eyes,
                self.threshold_eye_intensity,
                self.threshold_eye_area_min_pix2,
                self.threshold_eye_area_max_pix2
            ),
            right_eye = None
        )

        return tracking

