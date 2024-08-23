from image_tools import FishInfo
import cv2
import json
from PyQt5.QtWidgets import QApplication
from typing import Callable

def open_loop_coords(
    camera_constructor: Callable,
    exposure_microsec: int,
    gain: float,
    fps: int,
    height: int,
    width: int,
    offset_x: int,
    offset_y: int,
    openloop_file: str,
    ):

    camera = camera_constructor()
    camera.set_exposure(exposure_microsec)
    camera.set_gain(gain)
    camera.set_framerate(fps)
    camera.set_height(height)
    camera.set_width(width)
    camera.set_offsetX(offset_x)
    camera.set_offsetY(offset_y)

    camera.start_acquisition() 
    frame = camera.get_frame()
    camera.stop_acquisition()
    image = frame.image

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
        gain=CAM_GAIN,
        fps=CAM_FPS,
        height=CAM_HEIGHT,
        width=CAM_WIDTH,
        offset_x=CAM_OFFSETX,
        offset_y=CAM_OFFSETY,
        openloop_file=OPEN_LOOP_DATAFILE,
    )    
