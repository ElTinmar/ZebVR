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

    with open(calibration_file, 'w') as f:
        json.dump(px_per_mm, f)

if __name__ == '__main__':

    from ZebVR.config import (
        CAMERA_CONSTRUCTOR,
        CAM_HEIGHT,
        CAM_WIDTH,
        CALIBRATION_CAM_EXPOSURE_MS,
        CALIBRATION_CAM_FPS, 
        CAM_GAIN, 
        CAM_OFFSETX, 
        CAM_OFFSETY, 
        CALIBRATION_SQUARE_SIZE_MM, 
        CALIBRATION_CHECKER_SIZE
    )

    pix_per_mm(
        camera_constructor=CAMERA_CONSTRUCTOR,
        exposure_microsec=CALIBRATION_CAM_EXPOSURE_MS,
        cam_gain=CAM_GAIN,
        cam_fps=CALIBRATION_CAM_FPS,
        cam_height=CAM_HEIGHT,
        cam_width=CAM_WIDTH,
        cam_offset_x=CAM_OFFSETX,
        cam_offset_y=CAM_OFFSETY,
        checker_grid_size=CALIBRATION_CHECKER_SIZE,
        checker_square_size_mm=CALIBRATION_SQUARE_SIZE_MM,
        calibration_file='calibration.json'
    )
    