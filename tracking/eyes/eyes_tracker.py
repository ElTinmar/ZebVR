import numpy as np
from typing import Tuple
from numpy.typing import NDArray
from tracking.utils.conncomp_filter import bwareafilter
from skimage.measure import label, regionprops
from core.abstractclasses import Tracker
from core.dataclasses import EyeTracking, EyeParam, Rect
from tracking.utils.geometry import ellipse_direction, angle_between_vectors
from tracking.utils.diagonal_imcrop import diagonal_crop

# TODO convert crop_dimension_pix in mm
class EyesTracker(Tracker):
    def __init__(
        self,
        pixels_per_mm: float,
        threshold_eye_intensity: float,
        dynamic_cropping_len_mm: float = 5,
        threshold_eye_area_min_mm2: float = 2,
        threshold_eye_area_max_mm2: float = 10,
        dist_eye_midline_mm: float = 0.1,
        crop_dimension_mm: Tuple = (1.2, 0.8),
        crop_offset_mm: float = 0
    ) -> None:
        
        super().__init__()
        self.pixels_per_mm = pixels_per_mm
        self.threshold_eye_intensity = threshold_eye_intensity
        self.threshold_eye_area_min_pix2 = threshold_eye_area_min_mm2 * pixels_per_mm
        self.threshold_eye_area_max_pix2 = threshold_eye_area_max_mm2 * pixels_per_mm
        self.dist_eye_midline_pix = dist_eye_midline_mm * pixels_per_mm
        self.dynamic_cropping_len_pix = int(np.ceil(dynamic_cropping_len_mm * pixels_per_mm))
        self.crop_dimension_pix = (
            int(crop_dimension_mm[0] * pixels_per_mm),
            int(crop_dimension_mm[1] * pixels_per_mm)
        )
        self.crop_offset_pix = crop_offset_mm * pixels_per_mm
        
                
    @staticmethod
    def get_eye_prop(blob) -> EyeParam:
        eye_dir = ellipse_direction(blob.inertia_tensor)
        vertical_axis = np.array([0, 1], dtype=np.float32)
        eye_angle = angle_between_vectors(eye_dir,vertical_axis)
        # (row,col) to (x,y) coordinates 
        y, x = blob.centroid
        eye_centroid = np.array([x, y],dtype = np.float32)
        res = EyeParam(
            direction = eye_dir, 
            angle = eye_angle, 
            centroid = eye_centroid
        )
        return res
            
    @staticmethod
    def track_eye(
        image: NDArray,
        threshold_eye_intensity: float, 
        threshold_eye_area_min_pix2: float,
        threshold_eye_area_max_pix2: float,
        dist_eye_midline_pix: float,
        x_midline: int
    ):
        
        eye_mask = bwareafilter(
            image >= threshold_eye_intensity, 
            min_size = threshold_eye_area_min_pix2, 
            max_size = threshold_eye_area_max_pix2
        )

        label_img = label(eye_mask)
        regions = regionprops(label_img) 
        left_eye = None
        right_eye = None
        for blob in regions:
            # (row,col) to (x,y) coordinates 
            y, x = blob.centroid
            if (x - x_midline) < -dist_eye_midline_pix:
                left_eye = EyesTracker.get_eye_prop(blob)
            elif (x - x_midline) > dist_eye_midline_pix:
                right_eye = EyesTracker.get_eye_prop(blob)

        tracking = EyeTracking(
            left_eye = left_eye,
            right_eye = right_eye,
            eye_mask = eye_mask,
            image = image
        )

        return tracking

    def track(
            self, 
            image: NDArray, 
            centroid: NDArray, 
            heading: NDArray
        ) -> EyeTracking:

        if centroid is not None:
            angle = np.arctan2(heading[1,1],heading[0,1]) 
            w, h = self.crop_dimension_pix
            corner = centroid - w//2 * heading[:,1] + (h+self.crop_offset_pix) * heading[:,0] 
            image = diagonal_crop(
                image, 
                Rect(corner[0],corner[1],w,h),
                np.rad2deg(angle)
            )

            tracking = EyesTracker.track_eye(
                image,
                self.threshold_eye_intensity, 
                self.threshold_eye_area_min_pix2,
                self.threshold_eye_area_max_pix2,
                self.dist_eye_midline_pix,
                w//2
            )

            return tracking
        return None

 
