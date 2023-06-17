from core.VR import VR
from core.dataclasses import CameraParameters
from devices.camera.dummycam import FromFile
from devices.projector.opencv_projector import CVProjector
from background.background import DynamicBackground
from tracking.body.body_tracker import BodyTracker
from tracking.eyes.eyes_tracker import EyesTracker
from tracking.tail.tail_tracker import TailTracker
from tracking.prey.prey_tracker import PreyTracker
from tracking.tracker_collection import TrackerCollection 
from tracking.display import TrackerDisp
from registration.registration_cam2proj import Cam2ProjReg
from visual_stimuli.phototaxis import Phototaxis 
from writers.video import CVWriter

# TODO this should be part of camera calibration
cam_pixels_per_mm = 50
cam_mm_per_pixel = 1/cam_pixels_per_mm

camera_param = CameraParameters(
    ROI_height = 1088,
    ROI_width = 1088,
    fps = 100
)
camera = FromFile(
    video_file = 'toy_data/behavior_2000.avi',
    parameters = camera_param
)

projector = CVProjector(monitor_id = 1)
projector.init_window()

background = DynamicBackground(
    width = int(camera_param.ROI_width),
    height = int(camera_param.ROI_height),
    num_images = 200, 
    every_n_image = 2
)

cam2proj = Cam2ProjReg(
    camera, 
    projector,
    num_frames_per_pt = 10, 
    grid_size_x = 10,
    grid_size_y = 10, 
    dot_radius = 5,
    dot_intensity = 255,
    ksize = 10
)
body_tracker = BodyTracker(
    threshold_body_intensity = 0.2,
    dynamic_cropping_len_mm = 3,
    pixels_per_mm = cam_pixels_per_mm,
    rescale = 0.25
)
eyes_tracker = EyesTracker(
    pixels_per_mm = cam_pixels_per_mm,
    dynamic_cropping_len_mm = 4,
    threshold_eye_intensity = 0.4,
    crop_dimension_pix = (60,40)
)
tail_tracker = TailTracker(
    dynamic_cropping_len_mm = 4,
    pixels_per_mm = cam_pixels_per_mm,
    n_tail_points = 12,
    ksize = 5,
    arc_angle_deg = 120,
    n_pts_interp = 40,
    n_pts_arc = 20
)
prey_tracker = PreyTracker(
    threshold_prey_intensity = 0.025,
    pixels_per_mm = cam_pixels_per_mm
)

tracker = TrackerCollection(body_tracker, [eyes_tracker, tail_tracker])
tracker_display = TrackerDisp(pixels_per_mm = cam_pixels_per_mm)

stimulus = Phototaxis(screenid=0)
"""
writer = CVWriter(
    height = camera_param.ROI_height,
    width = camera_param.ROI_width,
    fps = 100,
    filename = '/home/martin/Documents/tracking2.avi'
)
"""

VirtualReality = VR(
    camera, 
    projector, 
    background, 
    cam2proj, 
    tracker, 
    tracker_display,
    stimulus,
    None
)
