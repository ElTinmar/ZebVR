import os
from video_tools import Polarity
import numpy as np
from functools import partial
#from lightcrafter import set_lcr_video_mode
from camera_tools import OpenCV_Webcam, MovieFileCam
try:
    from camera_tools import XimeaCamera 
except:
    print('Ximea camera not imported')

DEBUG = False

# general settings
LCr = False
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
    #set_lcr_video_mode()
else:
    PROJ_HEIGHT = 1080
    PROJ_WIDTH = 1920
    PIXEL_SCALING = (1.0, 1.0)

PROJ_POS = (1080, 0)
PROJ_FPS = 240
FOREGROUND_COLOR = (1.0, 0.0, 0.0, 1.0)
BACKGROUND_COLOR = (0.0, 0.0, 0.0, 1.0)

# camera
if not DEBUG:
    CAMERA_CONSTRUCTOR = XimeaCamera
CAM_HEIGHT = 512
CAM_WIDTH = 512
CAM_OFFSETX = 768
CAM_OFFSETY = 768
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
DETECTION_THRESHOLD = 0.15
CONTRAST = 1
GAMMA = 1
BRIGHTNESS = 0
BLUR_SIZE_PX = 1
DOT_RADIUS = 1
BAR_STEPS = 200
DOT_STEPS = 11
CAM_REGISTRATION_EXPOSURE_MS = 1_000
CAM_REGISTRATION_BARS_FPS = 30
CAM_REGISTRATION_DOTS_FPS = 5
PATTERN_INTENSITY = 128

# pix/mm
CALIBRATION_SQUARE_SIZE_MM = 1
CALIBRATION_CAM_EXPOSURE_MS = 15_000
CALIBRATION_CAM_FPS = 10
CALIBRATION_CHECKER_SIZE = (9, 6)
CALIBRATION_CHECK_DIAMETER_MM = [15, 30, 45, 60]
PIX_PER_MM = 40.902

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

BODY_TRACKING = True
BODY_TRACKING_PARAM = {
    'pix_per_mm': PIX_PER_MM,
    'target_pix_per_mm': 10,
    'body_intensity': 0.1,
    'body_brightness': 0.0,
    'body_gamma': 1.0,
    'body_contrast': 3.0,
    'min_body_size_mm': 5.0,
    'max_body_size_mm': 300.0,
    'min_body_length_mm': 0,
    'max_body_length_mm': 0,
    'min_body_width_mm': 0,
    'max_body_width_mm': 0,
    'blur_sz_mm': 1/7.5,
    'median_filter_sz_mm': 0
}

EYES_TRACKING = False
EYES_TRACKING_PARAM = {
    'pix_per_mm': PIX_PER_MM,
    'target_pix_per_mm': 40,
    'eye_thresh_lo': 0.3,
    'eye_thresh_hi': 0.7,
    'eye_dyntresh_res': 5,
    'eye_brightness': 0.0,
    'eye_gamma': 3.0,
    'eye_contrast': 5.0,
    'eye_size_lo_mm': 0.8,
    'eye_size_hi_mm': 10.0,
    'crop_offset_mm': -0.75,
    'crop_dimension_mm': (1.0, 1.5),
    'blur_sz_mm': 0.06,
    'median_filter_sz_mm': 0
}

TAIL_TRACKING = False
TAIL_TRACKING_PARAM = {
    'pix_per_mm': PIX_PER_MM,
    'target_pix_per_mm': 20,
    'tail_brightness': 0.0,
    'tail_gamma': 0.75,
    'tail_contrast': 3.0,
    'ball_radius_mm': 0.05,
    'arc_angle_deg': 90,
    'n_pts_arc': 20,
    'n_tail_points': 6,
    'n_pts_interp': 40,
    'tail_length_mm': 2.2,
    'dist_swim_bladder_mm': 0.0,
    'crop_dimension_mm': (3.5, 3.5),
    'crop_offset_tail_mm': 1.75,
    'blur_sz_mm': 0.06,
    'median_filter_sz_mm': 0
}

# Display
DISPLAY_FPS = 30
DOWNSAMPLE_TRACKING_EXPORT = 0.5

# Phototaxis
PHOTOTAXIS_POLARITY = 1

# OMR
OMR_SPATIAL_PERIOD_MM = 10
OMR_SPEED_MM_PER_SEC = 10
OMR_ANGLE_DEG = 90

# OKR
OKR_SPATIAL_FREQUENCY_DEG = 45
OKR_SPEED_DEG_PER_SEC = 60

# Loomings
LOOMING_CENTER_MM = (0, 10)
LOOMING_PERIOD_SEC = 10
LOOMING_EXPANSION_TIME_SEC = 10
LOOMING_EXPANSION_SPEED_MM_PER_SEC = 20


if DEBUG:
    movie_file = os.path.abspath(os.path.join(os.getcwd(), "../toy_data/single_freelyswimming_504x500px.avi"))
    mov = partial(MovieFileCam, filename=movie_file)

    CAMERA_CONSTRUCTOR = mov 
    CAM_HEIGHT = 500
    CAM_WIDTH = 504
    PROJ_HEIGHT = 500
    PROJ_WIDTH = 504
    CAM_FPS = 100
    PIXEL_SCALING = (1.0, 1.0)
    EYES_TRACKING = True
    TAIL_TRACKING = True

