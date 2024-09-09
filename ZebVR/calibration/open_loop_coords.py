from image_tools import FishInfo
import cv2
import json
from PyQt5.QtWidgets import QApplication
from typing import Callable

def open_loop_coords(
    camera_constructor: Callable,
    exposure_microsec: int,
    cam_gain: float,
    cam_fps: int,
    cam_height: int,
    cam_width: int,
    cam_offset_x: int,
    cam_offset_y: int,
    openloop_file: str,
    ):

    camera = camera_constructor()
    camera.set_exposure(exposure_microsec)
    camera.set_gain(cam_gain)
    camera.set_framerate(cam_fps)
    camera.set_height(cam_height)
    camera.set_width(cam_width)
    camera.set_offsetX(cam_offset_x)
    camera.set_offsetY(cam_offset_y)

    camera.start_acquisition() 
    frame = camera.get_frame()
    camera.stop_acquisition()
    image = frame['image']

    # get centroid, heading, maybe eye position
    app = QApplication([])
    window = FishInfo(image)
    window.show()
    app.exec()

    data = window.get_data()

    with open(openloop_file,'w') as f:
        json.dump(data, f)

if __name__ == '__main__':

    from ZebVR.config import (
        CAMERA_CONSTRUCTOR,
        CAM_WIDTH, 
        CAM_HEIGHT,
        CAM_EXPOSURE_MS, 
        CAM_GAIN, 
        CAM_FPS,
        CAM_OFFSETX, 
        CAM_OFFSETY, 
        OPEN_LOOP_DATAFILE,
    )

    open_loop_coords(
        camera_constructor=CAMERA_CONSTRUCTOR,
        exposure_microsec=CAM_EXPOSURE_MS,
        cam_gain=CAM_GAIN,
        cam_fps=CAM_FPS,
        cam_height=CAM_HEIGHT,
        cam_width=CAM_WIDTH,
        cam_offset_x=CAM_OFFSETX,
        cam_offset_y=CAM_OFFSETY,
        openloop_file=OPEN_LOOP_DATAFILE,
    )    
