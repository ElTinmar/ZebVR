import time
from video_tools import mode
import numpy as np
from tqdm import tqdm
from image_tools import im2single, im2gray
import cv2
from typing import Callable

RESIZED_HEIGHT = 512 # make sure that display fits on various screens

def static_background(
    camera_constructor: Callable,
    exposure_microsec: int,
    gain: float,
    fps: int,
    height: int,
    width: int,
    offset_x: int,
    offset_y: int,
    num_images: int,
    time_between_images: float,
    background_file: str,
):
    
    camera = camera_constructor()
    camera.set_exposure(exposure_microsec)
    camera.set_gain(gain)
    camera.set_framerate(fps)
    camera.set_height(height)
    camera.set_width(width)
    camera.set_offsetX(offset_x)
    camera.set_offsetY(offset_y)

    sample_frames = np.empty((height, width, num_images), dtype=np.float32)
    resized_width = int(RESIZED_HEIGHT * width/height)    
    cv2.namedWindow('acquisition')

    print('Acquiring images')
    for i in tqdm(range(num_images)):

        camera.start_acquisition() # need to restart acquisition to get the last frame 
        frame = camera.get_frame()
        camera.stop_acquisition()

        image = im2single(im2gray(frame.image))
        sample_frames[:,:,i] = image
        
        image_resized = cv2.resize(image,(resized_width,RESIZED_HEIGHT))
        cv2.imshow('acquisition', image_resized)
        cv2.waitKey(1)

        time.sleep(time_between_images)

    cv2.destroyWindow('acquisition')

    print('Compute background')
    background = mode(sample_frames)

    print('Background done, press key to save...')
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
        NUM_IMAGES, 
        TIME_BETWEEN_IMAGES, 
        CAMERA_CONSTRUCTOR
    )

    static_background(
        camera_constructor=CAMERA_CONSTRUCTOR,
        exposure_microsec=CAM_EXPOSURE_MS,
        gain=CAM_GAIN,
        fps=CAM_FPS,
        height=CAM_HEIGHT,
        width=CAM_WIDTH,
        offset_x=CAM_OFFSETX,
        offset_y=CAM_OFFSETY,
        background_file=BACKGROUND_FILE,
        num_images=NUM_IMAGES,
        time_between_images=TIME_BETWEEN_IMAGES
    )