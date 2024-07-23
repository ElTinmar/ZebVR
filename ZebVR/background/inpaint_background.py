from image_tools import DrawPolyMask, im2uint8
import numpy as np
import cv2
from PyQt5.QtWidgets import QApplication
from ZebVR.config import (
    CAM_WIDTH, CAM_HEIGHT,
    CAM_EXPOSURE_MS, CAM_GAIN, CAM_FPS,
    CAM_OFFSETX, CAM_OFFSETY, BACKGROUND_FILE,
    NUM_IMAGES, CAMERA_CONSTRUCTOR
)

if __name__ == '__main__':

    ALGO = cv2.INPAINT_NS
    RADIUS = 3

    camera = CAMERA_CONSTRUCTOR()
    camera.set_exposure(CAM_EXPOSURE_MS)
    camera.set_gain(CAM_GAIN)
    camera.set_framerate(CAM_FPS)
    camera.set_height(CAM_HEIGHT)
    camera.set_width(CAM_WIDTH)
    camera.set_offsetX(CAM_OFFSETX)
    camera.set_offsetY(CAM_OFFSETY)

    sample_frames = np.empty((CAM_HEIGHT, CAM_WIDTH, NUM_IMAGES), dtype=np.float32)

    camera.start_acquisition() 
    frame = camera.get_frame()
    camera.stop_acquisition()
    image = frame.image

    app = QApplication([])
    window = DrawPolyMask(image)
    window.show()
    app.exec()

    _,mask = window.get_masks()[1]
    background = cv2.inpaint(image, im2uint8(mask), RADIUS, ALGO)

    print('Background done, press key to save...')
    background_resized = cv2.resize(background,(512,512))
    cv2.imshow('background', background_resized)
    cv2.waitKey(0)

    print(f'Saving image to {BACKGROUND_FILE}')
    with open(BACKGROUND_FILE, 'wb') as f:
        np.save(f, background)
