from typing import Tuple 
import numpy as np
from numpy.typing import NDArray
import cv2
from utils.conncomp_filter import bwareafilter
from skimage.measure import label, regionprops
from dataclasses import dataclass

def ellipse_direction(inertia_tensor: NDArray) -> NDArray:
    # return the first eigenvector of the inertia tensor
    # corresponds to the principal axis of the ellipse 
    eigvals, eigvecs = np.linalg.eig(inertia_tensor)
    loc = np.argmax(abs(eigvals))
    return eigvecs[loc,:]

def angle_between_vectors(v1: NDArray, v2: NDArray) -> float:
    v1_unit = v1 / np.linalg.norm(v1)
    v2_unit = v2 / np.linalg.norm(v2)
    return np.arccos(np.dot(v1_unit,v2_unit))

@dataclass    
class eye_stats:
    direction: NDArray
    angle_to_heading: float
    centroid: NDArray
    
def get_eye_prop(regions, eye_ind, principal_components) -> eye_stats:
    if eye_ind.size > 0:
        eye_dir = ellipse_direction(regions[eye_ind].inertia_tensor)
        eye_angle = angle_between_vectors(eye_dir,principal_components[:,0])
        # (row,col) to (x,y) coordinates 
        eye_centroid = np.array([regions[eye_ind].centroid[1], regions[eye_ind].centroid[0]])
        return eye_stats(eye_dir, eye_angle, eye_centroid)
    else:
        return None

def eyes_tracker(
        frame: NDArray,
        threshold_eye_intensity: float,
        threshold_eye_area_min: int,
        threshold_eye_area_max: int,
        principal_components: NDArray,
        fish_centroid: NDArray
        ) -> Tuple[eye_stats, eye_stats, NDArray]:
    """
    Track the left and right eyes for a single fish
    Input: 
        frame: single precision, grayscale image as numpy array
    Output:
        (left,right): angle in radians for the left and right eye
        with respect to the anteroposterior axis 
    """

    eye_mask = bwareafilter(
        frame >= threshold_eye_intensity, 
        min_size = threshold_eye_area_min, 
        max_size = threshold_eye_area_max
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
    left_eye_index = np.squeeze(np.argwhere(np.logical_and(centroids_pc[:,0] > 10, centroids_pc[:,1] < -5)))
    right_eye_index = np.squeeze(np.argwhere(np.logical_and(centroids_pc[:,0] > 10, centroids_pc[:,1] > 5)))
    left_eye = get_eye_prop(regions, left_eye_index, principal_components)
    right_eye = get_eye_prop(regions, right_eye_index, principal_components)
        
    return (left_eye, right_eye, eye_mask)
