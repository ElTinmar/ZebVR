from image_tools import FishInfo, im2uint8
import cv2
import json
from PyQt5.QtWidgets import QApplication
from ZebVR.config import (
    CAM_WIDTH, CAM_HEIGHT,
    CAM_EXPOSURE_MS, CAM_GAIN, CAM_FPS,
    CAM_OFFSETX, CAM_OFFSETY, OPEN_LOOP_DATAFILE,
    CAMERA_CONSTRUCTOR
)

if __name__ == '__main__':

    camera = CAMERA_CONSTRUCTOR()
    camera.set_exposure(CAM_EXPOSURE_MS)
    camera.set_gain(CAM_GAIN)
    camera.set_framerate(CAM_FPS)
    camera.set_height(CAM_HEIGHT)
    camera.set_width(CAM_WIDTH)
    camera.set_offsetX(CAM_OFFSETX)
    camera.set_offsetY(CAM_OFFSETY)

    cv2.namedWindow('calibration')

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

    with open(OPEN_LOOP_DATAFILE,'w') as f:
        json.dump(data, f)
    
