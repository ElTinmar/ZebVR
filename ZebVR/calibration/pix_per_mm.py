import numpy as np
from camera_tools import get_camera_px_per_mm
from typing import Callable, Tuple

def pix_per_mm(
    camera_constructor: Callable,
    exposure_microsec: int,
    gain: float,
    fps: int,
    height: int,
    width: int,
    offset_x: int,
    offset_y: int,
    checker_grid_size: Tuple[int, int],
    checker_square_size_mm: float
):

    camera = camera_constructor()
    camera.set_exposure(exposure_microsec)
    camera.set_gain(gain)
    camera.set_framerate(fps)
    camera.set_height(height)
    camera.set_width(width)
    camera.set_offsetX(offset_x)
    camera.set_offsetY(offset_y)

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

    print(px_per_mm)

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
        gain=CAM_GAIN,
        fps=CALIBRATION_CAM_FPS,
        height=CAM_HEIGHT,
        width=CAM_WIDTH,
        offset_x=CAM_OFFSETX,
        offset_y=CAM_OFFSETY,
        checker_grid_size=CALIBRATION_CHECKER_SIZE,
        checker_square_size_mm=CALIBRATION_SQUARE_SIZE_MM
    )
    