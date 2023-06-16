import numpy as np
from numpy.typing import NDArray
from core.dataclasses import Rect
import cv2

def ellipse_direction(inertia_tensor: NDArray) -> NDArray:
    '''
    Get ellipse orientation: return the first eigenvector 
    of the inertia tensor, which corresponds to the principal 
    axis of the ellipse 
    '''
    eigvals, eigvecs = np.linalg.eig(inertia_tensor)
    loc = np.argmax(abs(eigvals))
    return eigvecs[loc,:]

def angle_between_vectors(v1: NDArray, v2: NDArray) -> float:
    v1_unit = v1 / np.linalg.norm(v1)
    v2_unit = v2 / np.linalg.norm(v2)
    return np.array(np.arccos(np.dot(v1_unit,v2_unit)))

def rotation_matrix(angle_deg: float) -> NDArray:
    angle_rad = np.deg2rad(angle_deg)
    M =  np.array(
        [
            [np.cos(angle_rad), -np.sin(angle_rad)],
            [np.sin(angle_rad), np.cos(angle_rad)]
        ]
    )
    return M

def rotate_vertices(rect: Rect, angle_deg: float) -> NDArray:
    ROI_vertices = np.array(
        [
            [0, 0],
            [0, rect.height],
            [rect.width, rect.height],
            [rect.width, 0],
        ], 
        dtype = np.float32
    )
    rotated_vertices = rotation_matrix(angle_deg) @ ROI_vertices.T
    rotated_vertices += np.array([[rect.left],[rect.bottom]])
    return rotated_vertices

def bounding_box_after_rot(rect: Rect, angle_deg: float) -> Rect:

    rotated_vertices = rotate_vertices(rect, angle_deg)

    # get bounding box coordinates
    bb_left = np.floor(min(rotated_vertices[0,:]))
    bb_right = np.ceil(max(rotated_vertices[0,:]))
    bb_bottom = np.floor(min(rotated_vertices[1,:]))
    bb_top = np.ceil(max(rotated_vertices[1,:]))
    bb_width = bb_right-bb_left
    bb_height = bb_top-bb_bottom

    return Rect(int(bb_left), int(bb_bottom), int(bb_width), int(bb_height))

def rotate_bounded(image: NDArray, angle_deg: float) -> NDArray:
    """
    Return rotated image with black regions
    """
    rectangle = Rect(0,0,image.shape[1],image.shape[0])
    bounding_box = bounding_box_after_rot(rectangle, angle_deg)
    angle_rad = np.deg2rad(angle_deg)
    transf_matrix = np.array(
        [
            [np.cos(angle_rad), -np.sin(angle_rad), -bounding_box.left],
            [np.sin(angle_rad), np.cos(angle_rad), -bounding_box.bottom]
        ]
    )
    image_rot = cv2.warpAffine(
        image, 
        transf_matrix, 
        [bounding_box.width, bounding_box.height]
    )
    return image_rot, bounding_box

def crop(image: NDArray, box: Rect) -> NDArray:
    return image[
        box.bottom:box.bottom+box.height, 
        box.left:box.left+box.width
    ]

def diagonal_crop(image: NDArray, rect: Rect, angle_deg: float) -> NDArray:

    bb = bounding_box_after_rot(rect, angle_deg)
    image_bb = crop(image, bb)
    image_rot, bb2 = rotate_bounded(image_bb, -angle_deg)

    [offsetx, offsety] = rotation_matrix(angle_deg) @ [[rect.left-bb.left],[rect.bottom-bb.bottom]]
    print([offsetx, offsety])

    print(rect)
    print(bb)
    print(bb2)
    bb3 = Rect(
        int(offsetx) - bb2.left,
        -int(offsety) - bb2.bottom,
        rect.width,
        rect.height
        )
    image_diag = crop(image_rot, bb3)
    return bb, image_bb, image_rot, image_diag