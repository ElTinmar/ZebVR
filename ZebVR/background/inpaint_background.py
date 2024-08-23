from image_tools import DrawPolyMask, im2uint8
import numpy as np
import cv2
from PyQt5.QtWidgets import QApplication
from typing import Callable

RESIZED_HEIGHT = 512 # make sure that display fits on various screens

def inpaint_background(
        camera_constructor: Callable,
        exposure_microsec: int,
        gain: float,
        fps: int,
        height: int,
        width: int,
        offset_x: int,
        offset_y: int,
        background_file: str,
        radius = 3, 
        algo = cv2.INPAINT_NS
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

    app = QApplication([])
    window = DrawPolyMask(image)
    window.setWindowTitle('Select region to infill. Left click to add points. Right click to close shape')
    window.show()
    app.exec()

    _,mask = window.get_masks()[1]
    background = cv2.inpaint(image, im2uint8(mask), radius, algo)

    print('Background done, press key to save...')
    resized_width = RESIZED_HEIGHT * width/height
    background_resized = cv2.resize(background,(resized_width,RESIZED_HEIGHT))
    cv2.imshow('background', background_resized)
    cv2.waitKey(10_000) 
    cv2.destroyAllWindows() 

    print(f'Saving image to {background_file}')
    with open(background_file, 'wb') as f:
        np.save(f, background)

if __name__ == '__main__':

    from ZebVR.config import (
        CAM_WIDTH,
        CAM_HEIGHT,
        CAM_EXPOSURE_MS, 
        CAM_GAIN, 
        CAM_FPS,
        CAM_OFFSETX, 
        CAM_OFFSETY, 
        BACKGROUND_FILE,
        CAMERA_CONSTRUCTOR
    )

    inpaint_background(
        camera_constructor=CAMERA_CONSTRUCTOR,
        exposure_microsec=CAM_EXPOSURE_MS,
        gain=CAM_GAIN,
        fps=CAM_FPS,
        height=CAM_HEIGHT,
        width=CAM_WIDTH,
        offset_x=CAM_OFFSETX,
        offset_y=CAM_OFFSETY,
        background_file=BACKGROUND_FILE,
        radius = 3,
        algo = cv2.INPAINT_NS
    )

 