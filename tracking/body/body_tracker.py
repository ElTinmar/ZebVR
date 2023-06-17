from typing import Tuple 
import numpy as np
from numpy.typing import NDArray
#from sklearnex import patch_sklearn
#patch_sklearn()
from sklearn.decomposition import PCA
from tracking.utils.conncomp_filter import bwareaopen
from core.abstractclasses import Tracker
import cv2
from core.dataclasses import BodyTracking, Rect

class BodyTracker(Tracker):

    def __init__(
            self, 
            threshold_body_intensity: float, 
            pixels_per_mm: float,
            threshold_body_area_mm2: float = 10,
            dynamic_cropping_len_mm: float = 4,
            rescale: float = None
        ) -> None:

        super().__init__()
        self.threshold_body_intensity = threshold_body_intensity
        self.previous_centroid = None
        self.pixels_per_mm = pixels_per_mm
        self.rescale = rescale
        self.threshold_body_area_pix2 = threshold_body_area_mm2 * pixels_per_mm
        self.dynamic_cropping_len_pix = int(np.ceil(dynamic_cropping_len_mm * pixels_per_mm))

    @staticmethod
    def track_pca(
            image: NDArray, 
            thresh_size: float, 
            thresh_intensity: float
        ) -> BodyTracking:

        # threshold and remove small objects 
        fish_mask = bwareaopen(
            image >= thresh_intensity, 
            min_size = thresh_size
        )
              
        blob_coordinates = np.argwhere(fish_mask) #  (row, col) coordinates

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
        
    def dynamic_cropping(self, image: NDArray) -> Tuple[NDArray, bool, Rect]:
        '''
        If previous centroid is defined, crop around it, otherwise
        return origingal image
        '''
        if self.previous_centroid is not None:
            left = int(max(self.previous_centroid[0] - self.dynamic_cropping_len_pix, 0))
            right = int(min(self.previous_centroid[0] + self.dynamic_cropping_len_pix, image.shape[1]))
            bottom = int(max(self.previous_centroid[1] - self.dynamic_cropping_len_pix, 0))
            top = int(min(self.previous_centroid[1] + self.dynamic_cropping_len_pix, image.shape[0]))
            width = right - left
            height = top - bottom
            return (image[bottom:top, left:right], True, Rect(left, bottom, width, height))
        else:
            return (image, False, None)

    def downsample_image(self, image: NDArray) -> Tuple[NDArray,bool]:
        '''
        If rescale is specified, return rescaled image with nearest
        neighbour interpolation, otherwise return original image
        '''
        if self.rescale is not None:
            image_resized = cv2.resize(
                image,
                None,
                fx = self.rescale, 
                fy = self.rescale,
                interpolation = cv2.INTER_NEAREST
            )
            return (image_resized, True)
        else:
            return (image, False)

    def get_original_coordinates(
            self, 
            coordinates: NDArray, 
            resized: bool, 
            cropped: bool,
            rect: Rect
        ):
        if resized:
            coordinates *= 1/self.rescale
        if cropped:
            coordinates += [rect.left, rect.bottom]
        return coordinates

    def track(self, image: NDArray) -> BodyTracking:

        image_ori = image.copy()
        image, cropped, rect = self.dynamic_cropping(image)
        image, resized = self.downsample_image(image)

        if resized:
            tracking = BodyTracker.track_pca(
                image = image, 
                thresh_size = self.threshold_body_area_pix2 * self.rescale**2,
                thresh_intensity = self.threshold_body_intensity
            )
        else:
            tracking = BodyTracker.track_pca(
                image = image, 
                thresh_size = self.threshold_body_area_pix2,
                thresh_intensity = self.threshold_body_intensity
            )
        
        if (tracking is None) and (cropped or resized):
            # if cropping or resizing failed, do the tracking on the whole image
            cropped = False
            resized = False
            tracking = self.track_pca(
                image = image_ori, 
                thresh_size = self.threshold_body_area_pix2,
                thresh_intensity = self.threshold_body_intensity
            )

        if tracking is not None: 
            tracking.centroid = self.get_original_coordinates(
                tracking.centroid,
                resized,
                cropped,
                rect
            )
            self.previous_centroid = tracking.centroid
        else:
            #self.previous_centroid = None
            pass

        return tracking