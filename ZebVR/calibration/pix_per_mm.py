import numpy as np
from camera_tools import get_camera_px_per_mm
from ZebVR.config import (
    CAM_WIDTH, CAM_HEIGHT,
    CAM_GAIN, CAM_OFFSETX, CAM_OFFSETY, CAMERA_CONSTRUCTOR,
    CALIBRATION_SQUARE_SIZE_MM, CALIBRATION_CAM_EXPOSURE_MS,
    CALIBRATION_CAM_FPS, CALIBRATION_CHECKER_SIZE
)

if __name__ == '__main__':

    camera = CAMERA_CONSTRUCTOR()
    camera.set_exposure(CALIBRATION_CAM_EXPOSURE_MS)
    camera.set_gain(CAM_GAIN)
    camera.set_framerate(CALIBRATION_CAM_FPS)
    camera.set_height(CAM_HEIGHT)
    camera.set_width(CAM_WIDTH)
    camera.set_offsetX(CAM_OFFSETX)
    camera.set_offsetY(CAM_OFFSETY)

    objp = np.zeros((np.prod(CALIBRATION_CHECKER_SIZE),3), np.float32)
    objp[:,:2] = np.mgrid[
        0:CALIBRATION_CHECKER_SIZE[0]*CALIBRATION_SQUARE_SIZE_MM:CALIBRATION_SQUARE_SIZE_MM,
        0:CALIBRATION_CHECKER_SIZE[1]*CALIBRATION_SQUARE_SIZE_MM:CALIBRATION_SQUARE_SIZE_MM
    ].T.reshape(-1,2)
    
    print(f"Press y to snap picture, and y to validate when checker is found. Press any key to cancel.")

    px_per_mm = get_camera_px_per_mm(
        cam=camera, 
        checkerboard_size=CALIBRATION_CHECKER_SIZE, 
        checkerboard_corners_world_coordinates_mm=objp,  
        camera_matrix=None,
        distortion_coef=None    
    )

    print(px_per_mm)