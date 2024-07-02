from camera_tools import XimeaCamera
import time
from video_tools import mode
import numpy as np
from tqdm import tqdm
from image_tools import im2single, im2gray
import cv2
from ZebVR.config import (
    CAM_WIDTH, CAM_HEIGHT,
    CAM_EXPOSURE_MS, CAM_GAIN, CAM_FPS,
    CAM_OFFSETX, CAM_OFFSETY, BACKGROUND_FILE,
    NUM_IMAGES, TIME_BETWEEN_IMAGES
)

if __name__ == '__main__':

    camera = XimeaCamera()
    camera.set_exposure(CAM_EXPOSURE_MS)
    camera.set_gain(CAM_GAIN)
    camera.set_framerate(CAM_FPS)
    camera.set_height(CAM_HEIGHT)
    camera.set_width(CAM_WIDTH)
    camera.set_offsetX(CAM_OFFSETX)
    camera.set_offsetY(CAM_OFFSETY)

    sample_frames = np.empty((CAM_HEIGHT, CAM_WIDTH, NUM_IMAGES), dtype=np.float32)
    cv2.namedWindow('acquisition')

    print('Acquiring images')
    for i in tqdm(range(NUM_IMAGES)):

        camera.start_acquisition() # looks like I need to restart to get the last frame with OpenCV...
        frame = camera.get_frame()
        camera.stop_acquisition()

        image = im2single(im2gray(frame.image))
        sample_frames[:,:,i] = image

        image_resized = cv2.resize(image,(512,512))
        cv2.imshow('acquisition', image_resized)
        cv2.waitKey(1)

        time.sleep(TIME_BETWEEN_IMAGES)

    cv2.destroyWindow('acquisition')

    print('Compute background')
    background = mode(sample_frames)

    print('Background done, press key to save...')
    background_resized = cv2.resize(background,(512,512))
    cv2.imshow('background', background_resized)
    cv2.waitKey(0)

    print(f'Saving image to {BACKGROUND_FILE}')
    with open(BACKGROUND_FILE, 'wb') as f:
        np.save(f, background)
