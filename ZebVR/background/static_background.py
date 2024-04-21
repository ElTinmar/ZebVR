from camera_tools import OpenCV_Webcam
import time
from video_tools import mode
import numpy as np
from tqdm import tqdm
from image_tools import im2single, im2gray
import cv2

if __name__ == '__main__':

    CAM_EXPOSURE_MS = 1000
    CAM_GAIN = 0
    CAM_FPS = 10
    CAM_HEIGHT = 480
    CAM_WIDTH = 640
    CAM_OFFSETX = 0
    CAM_OFFSETY = 0
    
    NUM_IMAGES = 20
    TIME_BETWEEN_IMAGES = 1

    BACKGROUND_FILE = 'background.npy'

    camera = OpenCV_Webcam()
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
        cv2.imshow('acquisition', image)
        cv2.waitKey(1)

        time.sleep(TIME_BETWEEN_IMAGES)

    cv2.destroyWindow('acquisition')

    print('Compute background')
    background = mode(sample_frames)

    print('Bavkground done, press key to save...')
    cv2.imshow('background', background)
    cv2.waitKey(0)

    print(f'Saving image to {BACKGROUND_FILE}')
    with open(BACKGROUND_FILE, 'wb') as f:
        np.save(f, background)
