import os
from video_tools import Polarity
import numpy as np
from functools import partial
#from ZebVR.lightcrafter import set_lcr_video_mode
from camera_tools import OpenCV_Webcam, MovieFileCam
try:
    from camera_tools import XimeaCamera 
except:
    pass

# flags

# set only one of the 3 to True
USE_MOVIE = False
USE_WEBCAM = True
USE_XIMEA = False

LCr = False
RECORD_VIDEO = False
OPEN_LOOP = False
BACKGROUND_GPU = False

# general settings
N_BACKGROUND_WORKERS = 1
N_TRACKER_WORKERS = 1
T_REFRESH = 1e-4

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

CAM_EXPOSURE_MS = 3000
CAM_GAIN = 0
CAM_OFFSETX = 0
CAM_OFFSETY = 0

if USE_MOVIE:
    movie_file = os.path.abspath(os.path.join(os.getcwd(), "../toy_data/single_freelyswimming_504x500px.avi"))
    mov = partial(MovieFileCam, filename=movie_file)

    CAMERA_CONSTRUCTOR = mov 
    CAM_HEIGHT = 500
    CAM_WIDTH = 504
    PROJ_HEIGHT = 500
    PROJ_WIDTH = 504
    CAM_FPS = 100

if USE_XIMEA:
    CAMERA_CONSTRUCTOR = XimeaCamera
    CAM_HEIGHT = 2048
    CAM_WIDTH = 2048
    CAM_OFFSETX = 0
    CAM_OFFSETY = 0
    CAM_GAIN = 0
    CAM_FPS = 60

if USE_WEBCAM:
    cam = partial(OpenCV_Webcam, cam_id=0)
    CAMERA_CONSTRUCTOR = cam 
    CAM_HEIGHT = 480
    CAM_WIDTH = 640
    CAM_FPS = 30

# files
LOGFILE_WORKERS = 'workers.log'
LOGFILE_QUEUES = 'queues.log'
OPEN_LOOP_DATAFILE = 'open_loop_coords.json'
REGISTRATION_FILE = 'registration.json'
BACKGROUND_FILE = 'background.npy'
IMAGE_FOLDER = os.path.join(os.getcwd(), 'recording_0')

# calibration
DETECTION_THRESHOLD = 0.15
CONTRAST = 1
GAMMA = 1
BRIGHTNESS = 0
BLUR_SIZE_PX = 1
DOT_RADIUS = 10
BAR_STEPS = 200
DOT_STEPS = 11
CAM_REGISTRATION_EXPOSURE_MS = 5_000
CAM_REGISTRATION_BARS_FPS = 30
CAM_REGISTRATION_DOTS_FPS = 5
PATTERN_INTENSITY = 128

# pix/mm
CALIBRATION_SQUARE_SIZE_MM = 2
CALIBRATION_CAM_EXPOSURE_MS = 15_000
CALIBRATION_CAM_FPS = 10
CALIBRATION_CHECKER_SIZE = (9, 6)
CALIBRATION_CHECK_DIAMETER_MM = [15, 30, 45, 60]
PIX_PER_MM = 38.773681409813456

# static background
NUM_IMAGES = 40
TIME_BETWEEN_IMAGES = 10
BACKGROUND_POLARITY = Polarity.DARK_ON_BRIGHT


N_PTS_INTERP = 40


# Display
DISPLAY_FPS = 30
DOWNSAMPLE_TRACKING_EXPORT = 0.5

# Recording
VIDEO_RECORDING_FPS = 20
VIDEO_RECORDING_COMPRESSION = True
VIDEO_RECORDING_RESIZE = 0.25



