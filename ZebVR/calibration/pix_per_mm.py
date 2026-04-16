import numpy as np
from camera_tools import get_camera_px_per_mm
from typing import Callable, Tuple
import json

def pix_per_mm(
    camera_constructor: Callable,
    exposure_microsec: int,
    cam_gain: float,
    cam_fps: int,
    cam_height: int,
    cam_width: int,
    cam_offset_x: int,
    cam_offset_y: int,
    checker_grid_size: Tuple[int, int],
    checker_square_size_mm: float,
    calibration_file: str
):

    camera = camera_constructor()
    camera.set_exposure(exposure_microsec)
    camera.set_gain(cam_gain)
    camera.set_framerate(cam_fps)
    camera.set_height(cam_height)
    camera.set_width(cam_width)
    camera.set_offsetX(cam_offset_x)
    camera.set_offsetY(cam_offset_y)

    objp = np.zeros((np.prod(checker_grid_size),3), np.float32)
    objp[:,:2] = np.mgrid[
        0:checker_grid_size[0]*checker_square_size_mm:checker_square_size_mm,
        0:checker_grid_size[1]*checker_square_size_mm:checker_square_size_mm
    ].T.reshape(-1,2)
    
    print(f"Press y to snap picture, and y to validate when checker is found. Press any key to cancel.")

    px_per_mm = get_camera_px_per_mm(
        cam=camera, 
        checkerboard_size=checker_grid_size, 
        checkerboard_corners_world_coordinates_mm=objp,  
        camera_matrix=None,
        distortion_coef=None    
    )

    if px_per_mm is None:
        return

    with open(calibration_file, 'w') as f:
        json.dump(float(px_per_mm), f)
