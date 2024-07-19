import os
from video_tools import Polarity
import numpy as np
from functools import partial
from camera_tools import OpenCV_Webcam, MovieFileCam
try:
    from camera_tools import XimeaCamera 
except:
    print('Ximea camera not imported')


# general settings
LCr = False #True
N_BACKGROUND_WORKERS = 1
N_TRACKER_WORKERS = 1
BACKGROUND_GPU = True
T_REFRESH = 1e-4
RECORD_VIDEO = False

# stimulus projection
if LCr:
    PROJ_HEIGHT = 1140
    PROJ_WIDTH = 912
    PIXEL_SCALING = (1.0, 0.5)
else:
    PROJ_HEIGHT = 800
    PROJ_WIDTH = 1280
    PIXEL_SCALING = (1.0, 1.0)

PROJ_POS = (2560,0)
PROJ_FPS = 60
FOREGROUND_COLOR = (1.0, 0.0, 0.0, 1.0)
BACKGROUND_COLOR = (0.0, 0.0, 0.0, 1.0)

# camera
movie_file = os.path.abspath(os.path.join(os.getcwd(), "../toy_data/single_freelyswimming_504x500px.avi"))
mov = partial(MovieFileCam, filename=movie_file)

CAMERA_CONSTRUCTOR = mov #XimeaCamera
CAM_HEIGHT = 500
CAM_WIDTH = 504
CAM_OFFSETX = 0
CAM_OFFSETY = 0
CAM_EXPOSURE_MS = 3000
CAM_GAIN = 0
CAM_FPS = 60

# files
LOGFILE_WORKERS = 'workers.log'
LOGFILE_QUEUES = 'queues.log'
REGISTRATION_FILE = 'registration.json'
BACKGROUND_FILE = 'background.npy'
IMAGE_FOLDER = os.path.join(os.getcwd(), 'recording_0')

# calibration
DETECTION_THRESHOLD = 0.4
CONTRAST = 3
GAMMA = 1.5
BRIGHTNESS = 0
BLUR_SIZE_PX = 3
DOT_RADIUS = 5
STEP_SIZE = 100
CAM_REGISTRATION_EXPOSURE_MS = 15_000
CAM_REGISTRATION_FPS = 10

# pix/mm
CALIBRATION_SQUARE_SIZE_MM = 3
CALIBRATION_CAM_EXPOSURE_MS = 15_000
CALIBRATION_CAM_FPS = 10
CALIBRATION_CHECKER_SIZE = (9,6)
CALIBRATION_CHECK_DIAMETER_MM = [15, 30, 45, 60]
PIX_PER_MM = 36.01

# static background
NUM_IMAGES = 40
TIME_BETWEEN_IMAGES = 10
BACKGROUND_POLARITY = Polarity.DARK_ON_BRIGHT

# tracking
ANIMAL_TRACKING_PARAM = {
    'pix_per_mm': PIX_PER_MM,
    'target_pix_per_mm': 5,
    'animal_intensity': 0.04,
    'animal_brightness': 0.0,
    'animal_gamma': 1.0,
    'animal_contrast': 1.0,
    'min_animal_size_mm': 2.0,
    'max_animal_size_mm': 300.0, 
    'min_animal_length_mm': 0,
    'max_animal_length_mm': 0,
    'min_animal_width_mm': 0,
    'max_animal_width_mm': 0,
    'blur_sz_mm': 1/5,
    'median_filter_sz_mm': 0
}

BODY_TRACKING_PARAM = {
    'pix_per_mm': PIX_PER_MM,
    'target_pix_per_mm': 10,
    'body_intensity': 0.1,
    'body_brightness': 0.0,
    'body_gamma': 1.0,
    'body_contrast': 3.0,
    'min_body_size_mm': 10.0,
    'max_body_size_mm': 300.0,
    'min_body_length_mm': 0,
    'max_body_length_mm': 0,
    'min_body_width_mm': 0,
    'max_body_width_mm': 0,
    'blur_sz_mm': 1/7.5,
    'median_filter_sz_mm': 0
}

# Phototaxis
PHOTOTAXIS_POLARITY = 1

# OMR
OMR_SPATIAL_FREQUENCY_DEG = 20
OMR_SPEED_DEG_PER_SEC = 180
OMR_ANGLE_DEG = 0

# OKR
OKR_SPATIAL_FREQUENCY_DEG = 45
OKR_SPEED_DEG_PER_SEC = 20

# Loomings
LOOMING_CENTER_MM = (1,1)
LOOMING_PERIOD_SEC = 60
LOOMING_EXPANSION_TIME_SEC = 10
LOOMING_EXPANSION_SPEED_MM_PER_SEC = 100