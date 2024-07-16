import os
from video_tools import Polarity
import numpy as np
from camera_tools import OpenCV_Webcam
try:
    from camera_tools import XimeaCamera 
except:
    print('Ximea camera not imported')

# general settings
LCr = False #True
N_BACKGROUND_WORKERS = 1
N_TRACKER_WORKERS = 1
BACKGROUND_GPU = False
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
FOREGROUND_COLOR = (1.0, 0, 0, 1.0)
BACKGROUND_COLOR = (0, 0, 0, 1.0)

# camera
CAMERA_CONSTRUCTOR = OpenCV_Webcam #XimeaCamera
CAM_HEIGHT = 480 #2048
CAM_WIDTH = 640 #2048
CAM_OFFSETX = 0
CAM_OFFSETY = 0
CAM_EXPOSURE_MS = 1000
CAM_GAIN = 0
CAM_FPS = 60

PIX_PER_MM = 34.36

# files
LOGFILE_WORKERS = 'workers.log'
LOGFILE_QUEUES = 'queues.log'
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
NUM_IMAGES = 40
TIME_BETWEEN_IMAGES = 10
POLARITY = Polarity.BRIGHT_ON_DARK #Polarity.DARK_ON_BRIGHT 

# tracking
ANIMAL_TRACKING_PARAM = {
    'pix_per_mm': PIX_PER_MM,
    'target_pix_per_mm': 5,
    'animal_intensity': 0.04,
    'animal_brightness': 0.0,
    'animal_gamma': 1.0,
    'animal_contrast': 1.0,
    'min_animal_size_mm': 2.0,
    'max_animal_size_mm': 240.0, # 60.0
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
    'max_body_size_mm': 60.0,
    'min_body_length_mm': 0,
    'max_body_length_mm': 0,
    'min_body_width_mm': 0,
    'max_body_width_mm': 0,
    'blur_sz_mm': 1/7.5,
    'median_filter_sz_mm': 0
}