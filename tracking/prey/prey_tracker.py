from typing import Tuple 
import numpy as np
from numpy.typing import NDArray
import cv2
from utils.conncomp_filter import bwareafilter
from skimage.measure import label, regionprops

def prey_tracker(
        frame: NDArray,
        threshold_prey_intensity: float,
        threshold_prey_area_min: int,
        threshold_prey_area_max: int,
        ) -> Tuple[NDArray, NDArray]:
    """
    Track the left and right eyes for a single fish
    Input: 
        frame: single precision, grayscale image as numpy array
    Output:
        (left,right): angle in radians for the left and right eye
        with respect to the anteroposterior axis 
    """

    prey_mask = bwareafilter(
        frame >= threshold_prey_intensity, 
        min_size = threshold_prey_area_min, 
        max_size = threshold_prey_area_max
    )

    label_img = label(prey_mask)
    regions = regionprops(label_img)

    prey_centroids = np.empty((len(regions),2),dtype=np.float32)
    for i,blob in enumerate(regions):
        prey_centroids[i,:] = [blob.centroid[1], blob.centroid[0]] 

    return (prey_centroids, prey_mask)