import numpy as np
from camera_tools import XimeaCamera, get_camera_px_per_mm
from ZebVR.config import (
    CAM_WIDTH, CAM_HEIGHT,
    CAM_GAIN, CAM_FPS,
    CAM_OFFSETX, CAM_OFFSETY
)

if __name__ == '__main__':

    CAM_EXPOSURE_MS = 20_000
    CAM_FPS = 5

    camera = XimeaCamera()
    camera.set_exposure(CAM_EXPOSURE_MS)
    camera.set_gain(CAM_GAIN)
    camera.set_framerate(CAM_FPS)
    camera.set_height(CAM_HEIGHT)
    camera.set_width(CAM_WIDTH)
    camera.set_offsetX(CAM_OFFSETX)
    camera.set_offsetY(CAM_OFFSETY)

    checker_sz = (9,6)
    square_sz_mm = 2

    objp = np.zeros((np.prod(checker_sz),3), np.float32)
    objp[:,:2] = np.mgrid[
        0:checker_sz[0]*square_sz_mm:square_sz_mm,
        0:checker_sz[1]*square_sz_mm:square_sz_mm
    ].T.reshape(-1,2)

    
    px_per_mm = get_camera_px_per_mm(
        cam=camera, 
        checkerboard_size=checker_sz, 
        checkerboard_corners_world_coordinates_mm=objp,  
        camera_matrix=None,
        distortion_coef=None,
        rescale=0.5
    )

    print(px_per_mm)