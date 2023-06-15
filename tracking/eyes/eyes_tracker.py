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
        body_tracker: BodyTracker,
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
        self.dynamic_cropping_len_pix = dynamic_cropping_len_mm * pixels_per_mm
        self.body_tracker = body_tracker
        self.rescale = rescale

        if rescale is not None:
            self.threshold_eye_area_min_pix2 *= rescale**2
            self.threshold_eye_area_max_pix2 *= rescale**2
            self.dist_eye_midline_pix *= rescale
            self.dist_eye_swimbladder_pix *= rescale
            self.dynamic_cropping_len_pix *= rescale

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
    
    def get_eye_prop(self, regions, eye_ind, principal_components) -> EyeParam:
        if eye_ind.size == 1:
            eye_dir = EyesTracker.ellipse_direction(regions[eye_ind].inertia_tensor)
            eye_angle = EyesTracker.angle_between_vectors(eye_dir,principal_components[:,0])
            # (row,col) to (x,y) coordinates 
            eye_centroid = np.array(
                [regions[eye_ind].centroid[1], 
                 regions[eye_ind].centroid[0]],
                dtype = np.float32
            )
            if self.rescale is not None:
                eye_centroid *= 1/self.rescale
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

        # tracking is faster on small images
        if self.rescale is not None:
            body_tracking.centroid *= self.rescale
            image = cv2.resize(
                    image, 
                    None, 
                    fx = self.rescale, 
                    fy = self.rescale,
                    interpolation=cv2.INTER_NEAREST
                )

        if body_tracking is not None:
            #TODO crop each eye separately instead 
            left = max(int(body_tracking.centroid[0]) - self.dynamic_cropping_len_pix, 0)
            right = min(int(body_tracking.centroid[0]) + self.dynamic_cropping_len_pix, image.shape[1])
            bottom = max(int(body_tracking.centroid[1]) - self.dynamic_cropping_len_pix, 0)
            top = min(int(body_tracking.centroid[1]) + self.dynamic_cropping_len_pix, image.shape[0])
            image = image[left:right,bottom:top]

            eye_mask = bwareafilter(
                image >= self.threshold_eye_intensity, 
                min_size = self.threshold_eye_area_min_pix2, 
                max_size = self.threshold_eye_area_max_pix2
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
                    centroids_pc[:,0] > self.dist_eye_swimbladder_pix, 
                    centroids_pc[:,1] < -self.dist_eye_midline_pix
                ))
            )
            right_eye_index = np.squeeze(
                np.argwhere(np.logical_and(
                    centroids_pc[:,0] > self.dist_eye_swimbladder_pix, 
                    centroids_pc[:,1] > self.dist_eye_midline_pix
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
