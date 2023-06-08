from typing import List 
import numpy as np
from numpy.typing import NDArray
from tracking.utils.conncomp_filter import bwareafilter
from skimage.measure import label, regionprops
from core.abstractclasses import Tracker
from tracking.body.body_tracker import BodyTrackerPCA
from core.dataclasses import EyeTracking, EyeParam
import cv2

class EyesTracker(Tracker):
    def __init__(
        self,
        threshold_body_intensity: float, 
        threshold_body_area: int,
        width: int,
        height: int,
        dynamic_cropping_len: int,
        threshold_eye_intensity: float,
        threshold_eye_area_min: int,
        threshold_eye_area_max: int,
        dist_eye_midline: int,
        dist_eye_swimbladder: int,
    ) -> None:
        
        super().__init__()
        self.threshold_eye_intensity = threshold_eye_intensity
        self.threshold_eye_area_min = threshold_eye_area_min
        self.threshold_eye_area_max = threshold_eye_area_max
        self.dist_eye_midline = dist_eye_midline 
        self.dist_eye_swimbladder = dist_eye_swimbladder
        self.dynamic_cropping_len = dynamic_cropping_len
        self.width = width
        self.height = height
        self.body_tracker = BodyTrackerPCA(
            threshold_body_intensity, 
            threshold_body_area,
            dynamic_cropping_len,
            height,
            width
        )

    @staticmethod
    def ellipse_direction(inertia_tensor: NDArray) -> NDArray:
    # return the first eigenvector of the inertia tensor
    # corresponds to the principal axis of the ellipse 
        eigvals, eigvecs = np.linalg.eig(inertia_tensor)
        loc = np.argmax(abs(eigvals))
        return eigvecs[loc,:]

    @staticmethod
    def angle_between_vectors(v1: NDArray, v2: NDArray) -> float:
        v1_unit = v1 / np.linalg.norm(v1)
        v2_unit = v2 / np.linalg.norm(v2)
        return np.array(np.arccos(np.dot(v1_unit,v2_unit)))
    
    @staticmethod
    def get_eye_prop(regions, eye_ind, principal_components) -> EyeParam:
        if eye_ind.size == 1:
            eye_dir = EyesTracker.ellipse_direction(regions[eye_ind].inertia_tensor)
            eye_angle = EyesTracker.angle_between_vectors(eye_dir,principal_components[:,0])
            # (row,col) to (x,y) coordinates 
            eye_centroid = np.array(
                [regions[eye_ind].centroid[1], 
                 regions[eye_ind].centroid[0]]
            )
            res = EyeParam(
                direction = eye_dir, 
                angle = eye_angle, 
                centroid = eye_centroid
            )
            return res
        else:
            return None

    def track(self, image: NDArray) -> EyeTracking:

        body_tracking = self.body_tracker.track(image)

        if body_tracking is not None:
            left = max(int(body_tracking.centroid[0]) - self.dynamic_cropping_len, 0)
            right = min(int(body_tracking.centroid[0]) + self.dynamic_cropping_len, self.width)
            bottom = max(int(body_tracking.centroid[1]) - self.dynamic_cropping_len, 0)
            top = min(int(body_tracking.centroid[1]) + self.dynamic_cropping_len, self.height)
            image = image[left:right,bottom:top]

            eye_mask = bwareafilter(
                image >= self.threshold_eye_intensity, 
                min_size = self.threshold_eye_area_min, 
                max_size = self.threshold_eye_area_max
            )

            label_img = label(eye_mask)
            regions = regionprops(label_img) # regionprops returns coordinates as (row, col) 

            blob_centroids = np.zeros((len(regions),2), dtype=np.float64)
            for i,blob in enumerate(regions):
                # (row,col) to (x,y) coordinates  
                blob_centroids[i,:] = [blob.centroid[1], blob.centroid[0]]

            # project coordinates to principal component space
            centroids_pc = (blob_centroids + [bottom, left] - body_tracking.centroid) @ body_tracking.heading

            # find the eyes TODO remove magic numbers and put as parameters
            left_eye_index = np.squeeze(
                np.argwhere(np.logical_and(
                    centroids_pc[:,0] > self.dist_eye_swimbladder, 
                    centroids_pc[:,1] < -self.dist_eye_midline
                ))
            )
            right_eye_index = np.squeeze(
                np.argwhere(np.logical_and(
                    centroids_pc[:,0] > self.dist_eye_swimbladder, 
                    centroids_pc[:,1] > self.dist_eye_midline
                ))
            )
            left_eye = EyesTracker.get_eye_prop(
                regions, 
                left_eye_index, 
                body_tracking.heading
            )
            if left_eye is not None:
                left_eye.centroid += [bottom, left]

            right_eye = EyesTracker.get_eye_prop(
                regions, 
                right_eye_index, 
                body_tracking.heading
            )
            if right_eye is not None:
                right_eye.centroid += [bottom, left]

            tracking = EyeTracking(
                left_eye = left_eye,
                right_eye = right_eye,
                eye_mask = eye_mask,
                body = body_tracking
            )

            return tracking
        else:
            return None
