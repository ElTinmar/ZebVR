from typing import List 
import numpy as np
from numpy.typing import NDArray
from tracking.utils.conncomp_filter import bwareafilter
from skimage.measure import label, regionprops
from core.abstractclasses import Tracker
from tracking.body.body_tracker import BodyTracker
from core.dataclasses import EyeTracking, EyeParam

import cv2

class EyesTracker(Tracker):
    def __init__(
        self,
        threshold_body_intensity: float, 
        threshold_body_area: int,
        threshold_eye_intensity: float,
        threshold_eye_area_min: int,
        threshold_eye_area_max: int,
        alpha: int = 100, 
        beta: int = 10,
        color_heading: tuple = (0,0,1),
        color_eye_left: tuple = (0,1,1),
        color_eye_right: tuple = (1,1,0)
    ) -> None:
        
        super().__init__()
        self.threshold_eye_intensity = threshold_eye_intensity
        self.threshold_eye_area_min = threshold_eye_area_min
        self.threshold_eye_area_max = threshold_eye_area_max
        self.body_tracker = BodyTracker(
            threshold_body_intensity, 
            threshold_body_area
        )

        self.curr_tracking = None

        self.alpha = alpha
        self.beta = beta
        self.color_heading = color_heading
        self.color_eye_left = color_eye_left
        self.color_eye_right = color_eye_right

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
            eye_mask = bwareafilter(
                image >= self.threshold_eye_intensity, 
                min_size = self.threshold_eye_area_min, 
                max_size = self.threshold_eye_area_max
            )

            label_img = label(eye_mask)
            regions = regionprops(label_img) # regionprops returns coordinates as (row, col) 

            blob_centroids = np.zeros((len(regions),2),dtype=np.float64)
            for i,blob in enumerate(regions):
                # (row,col) to (x,y) coordinates  
                blob_centroids[i,:] = [blob.centroid[1], blob.centroid[0]]

            # project coordinates to principal component space
            centroids_pc = (blob_centroids - body_tracking.centroid) @ body_tracking.heading

            # find the eyes TODO remove magic numbers and put as parameters
            left_eye_index = np.squeeze(
                np.argwhere(np.logical_and(centroids_pc[:,0] > 10, centroids_pc[:,1] < -5))
            )
            right_eye_index = np.squeeze(
                np.argwhere(np.logical_and(centroids_pc[:,0] > 10, centroids_pc[:,1] > 5))
            )
            left_eye = EyesTracker.get_eye_prop(
                regions, 
                left_eye_index, 
                body_tracking.heading
            )
            right_eye = EyesTracker.get_eye_prop(
                regions, 
                right_eye_index, 
                body_tracking.heading
            )

            self.curr_tracking = EyeTracking(
                left_eye = left_eye,
                right_eye = right_eye,
                eye_mask = eye_mask,
                body = body_tracking
            )

            return self.curr_tracking
        else:
            return None

    def tracking_overlay(self, image: NDArray) -> NDArray:

        overlay = np.zeros(
            (image.shape[0],image.shape[1],3), 
            dtype=np.single
        )

        if self.curr_tracking is not None:

            pt1 = self.curr_tracking.body.centroid
            pt2 = self.curr_tracking.body.centroid + \
                self.alpha * self.curr_tracking.body.heading[:,0]
            overlay = cv2.line(
                overlay,
                pt1.astype(np.int32),
                pt2.astype(np.int32),
                self.color_heading
            )

            if self.curr_tracking.left_eye is not None:
                pt1 = self.curr_tracking.left_eye.centroid
                pt2 = pt1 + self.beta * self.curr_tracking.left_eye.direction
                overlay = cv2.line(
                    overlay,
                    pt1.astype(np.int32),
                    pt2.astype(np.int32),
                    self.color_eye_left
                )
                pt2 = pt1 - self.beta * self.curr_tracking.left_eye.direction
                overlay = cv2.line(
                    overlay,
                    pt1.astype(np.int32),
                    pt2.astype(np.int32),
                    self.color_eye_left
                )

            if self.curr_tracking.right_eye is not None:
                pt1 = self.curr_tracking.right_eye.centroid
                pt2 = pt1 + self.beta * self.curr_tracking.right_eye.direction
                overlay = cv2.line(
                    overlay,
                    pt1.astype(np.int32),
                    pt2.astype(np.int32),
                    self.color_eye_right
                )
                pt2 = pt1 - self.beta * self.curr_tracking.right_eye.direction
                overlay = cv2.line(
                    overlay,
                    pt1.astype(np.int32),
                    pt2.astype(np.int32),
                    self.color_eye_right
                )

        return overlay