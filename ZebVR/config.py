import os
from video_tools import Polarity
import numpy as np

LCr = True

# general settings
if LCr:
    PROJ_HEIGHT = 1140
    PROJ_WIDTH = 912
    PIXEL_SCALING = (1.0, 0.5)
    # PIXEL_SCALING = (2*np.sqrt(2/5), np.sqrt(2/5)) # norm is still sqrt(2)
else:
    PROJ_HEIGHT = 800
    PROJ_WIDTH = 1280
    PIXEL_SCALING = (1.0, 1.0)

PROJ_POS = (2560,0)

CAM_HEIGHT = 2048
CAM_WIDTH = 2048
CAM_OFFSETX = 0
CAM_OFFSETY = 0
CAM_EXPOSURE_MS = 1000
CAM_GAIN = 0
CAM_FPS = 30

PIX_PER_MM = 34.36

# files
CALIBRATION_FILE = 'registration.json'
BACKGROUND_FILE = 'background.npy'
IMAGE_FOLDER = os.path.join(os.getenv('HOME'), 'Development/ZebVR/recording_0')

# calibration
DETECTION_THRESHOLD = 0.4
CONTRAST = 3
GAMMA = 1.5
BRIGHTNESS = 0
BLUR_SIZE_PX = 3
DOT_RADIUS = 5
STEP_SIZE = 100

# static background
NUM_IMAGES = 20
TIME_BETWEEN_IMAGES = 1
POLARITY = Polarity.DARK_ON_BRIGHT

# tracking
ANIMAL_TRACKING_PARAM = {
    'pix_per_mm': PIX_PER_MM,
    'target_pix_per_mm': 5,
    'animal_intensity': 0.07,
    'animal_brightness': 0.0,
    'animal_gamma': 1.0,
    'animal_contrast': 1.0,
    'min_animal_size_mm': 3.0,
    'max_animal_size_mm': 30.0,
    'min_animal_length_mm': 0,
    'max_animal_length_mm': 0,
    'min_animal_width_mm': 0,
    'max_animal_width_mm': 0,
    'pad_value_mm': 2.75,
    'blur_sz_mm': 1/5,
    'median_filter_sz_mm': 0
}

BODY_TRACKING_PARAM = {
    'pix_per_mm': PIX_PER_MM,
    'target_pix_per_mm': 10,
    'body_intensity': 0.20,
    'body_brightness': 0.0,
    'body_gamma': 1.0,
    'body_contrast': 3.0,
    'min_body_size_mm': 3.0,
    'max_body_size_mm': 30.0,
    'min_body_length_mm': 0,
    'max_body_length_mm': 0,
    'min_body_width_mm': 0,
    'max_body_width_mm': 0,
    'blur_sz_mm': 1/7.5,
    'median_filter_sz_mm': 0
}