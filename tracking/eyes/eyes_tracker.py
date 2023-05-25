from typing import List 
import numpy as np
from numpy.typing import NDArray
from tracking.utils.conncomp_filter import bwareafilter
from skimage.measure import label, regionprops
from core.abstractclasses import Tracker
from tracking.body.body_tracker import BodyTracker
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

        self.left_eye = None
        self.right_eye = None
        self.eye_mask = None
        self.fish_centroid = None
        self.principal_components = None
        self.fish_mask = None

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
    def get_eye_prop(regions, eye_ind, principal_components) -> List[NDArray]:
        if eye_ind.size == 1:
            eye_dir = EyesTracker.ellipse_direction(regions[eye_ind].inertia_tensor)
            eye_angle = EyesTracker.angle_between_vectors(eye_dir,principal_components[:,0])
            # (row,col) to (x,y) coordinates 
            eye_centroid = np.array(
                [regions[eye_ind].centroid[1], 
                 regions[eye_ind].centroid[0]]
            )
            return [eye_dir, eye_angle, eye_centroid]
        else:
            return [None, None, None]

    def track(self, image: NDArray) -> List[NDArray]:

        [fish_centroid, principal_components, fish_mask] = self.body_tracker.track(image)

        if fish_centroid is not None:
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
            centroids_pc = (blob_centroids - fish_centroid) @ principal_components

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
                principal_components
            )
            right_eye = EyesTracker.get_eye_prop(
                regions, 
                right_eye_index, 
                principal_components
            )

            self.left_eye = left_eye
            self.right_eye = right_eye
            self.eye_mask = eye_mask
            self.fish_centroid = fish_centroid
            self.principal_components = principal_components
            self.fish_mask = fish_mask

            return [left_eye, right_eye, eye_mask, fish_centroid, principal_components, fish_mask]
        else:
            self.left_eye = None
            self.right_eye = None
            self.eye_mask = None
            self.fish_centroid = None
            self.principal_components = None
            self.fish_mask = None

            return [None, None, None, None, None, None]

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

            if self.left_eye[0] is not None:
                pt1 = self.left_eye[2]
                pt2 = pt1 + self.beta*self.left_eye[0]
                overlay = cv2.line(
                    overlay,
                    pt1.astype(np.int32),
                    pt2.astype(np.int32),
                    self.color_eye_left
                )
                pt2 = pt1 - self.beta*self.left_eye[0]
                overlay = cv2.line(
                    overlay,
                    pt1.astype(np.int32),
                    pt2.astype(np.int32),
                    self.color_eye_left
                )

            if self.right_eye[0] is not None:
                pt1 = self.right_eye[2]
                pt2 = pt1 + self.beta*self.right_eye[0]
                overlay = cv2.line(
                    overlay,
                    pt1.astype(np.int32),
                    pt2.astype(np.int32),
                    self.color_eye_right
                )
                pt2 = pt1 - self.beta*self.right_eye[0]
                overlay = cv2.line(
                    overlay,
                    pt1.astype(np.int32),
                    pt2.astype(np.int32),
                    self.color_eye_right
                )

        return overlay