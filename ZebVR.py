from core.VR import VR
from core.dataclasses import CameraParameters
from devices.camera.dummycam import FromFile
from devices.projector.opencv_projector import CVProjector
from background.background import DynamicBackground
from tracking.body.body_tracker import BodyTrackerPCA
from tracking.eyes.eyes_tracker import EyesTracker
from tracking.tail.tail_tracker import TailTracker
from tracking.prey.prey_tracker import PreyTracker
from tracking.tracker_collection import TrackerCollection 
from tracking.display import TrackerDisp
from registration.registration_cam2proj import Cam2ProjReg
from visual_stimuli.phototaxis import Phototaxis 
from writers.video import CVWriter

rescale = 1

# TODO this should be part of camera calibration
cam_pixels_per_mm = 40
cam_mm_per_pixel = 1/cam_pixels_per_mm

camera_param = CameraParameters(
    ROI_height = 2048,
    ROI_width = 2048,
    fps = 100
)
camera = FromFile(
    video_file = 'toy_data/50mm2_mjpeg.avi',
    parameters = camera_param,
    rescale = None
)

projector = CVProjector(monitor_id = 1)
projector.init_window()

background = DynamicBackground(
    width = int(camera_param.ROI_width*rescale),
    height = int(camera_param.ROI_height*rescale),
    num_images = 100, 
    every_n_image = 20
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

body_tracker = BodyTrackerPCA(
    threshold_body_intensity = 0.05,
    threshold_body_area = 10 * cam_pixels_per_mm * rescale**2,
    width = int(camera_param.ROI_width*rescale),
    height = int(camera_param.ROI_height*rescale),
    dynamic_cropping_len = int(10 * cam_pixels_per_mm)
)
eyes_tracker = EyesTracker(
    threshold_body_intensity = 0.05,
    threshold_body_area = 10 * cam_pixels_per_mm * rescale**2,
    width = int(camera_param.ROI_width*rescale),
    height = int(camera_param.ROI_height*rescale),
    dynamic_cropping_len = int(10 * cam_pixels_per_mm),
    threshold_eye_intensity = 0.2,
    threshold_eye_area_min = 2 * cam_pixels_per_mm * rescale**2,
    threshold_eye_area_max = 10 * cam_pixels_per_mm * rescale**2,
    dist_eye_midline = 0.1 * cam_pixels_per_mm * rescale,
    dist_eye_swimbladder = 0.2 * cam_pixels_per_mm * rescale
)
tail_tracker = TailTracker(
    threshold_body_intensity = 0.05,
    threshold_body_area = 10 * cam_pixels_per_mm * rescale**2,
    width = int(camera_param.ROI_width*rescale),
    height = int(camera_param.ROI_height*rescale),
    dynamic_cropping_len = int(10 * cam_pixels_per_mm),
    tail_length = 6 * cam_pixels_per_mm * rescale,
    n_tail_points = 12,
    ksize = 5,
    arc_angle_deg = 150,
    n_pts_interp = 40,
    n_pts_arc = 20
)
prey_tracker = PreyTracker(
    threshold_prey_intensity = 0.025,
    threshold_prey_area_min = 0.3 * cam_pixels_per_mm * rescale**2,
    threshold_prey_area_max = 2 * cam_pixels_per_mm *rescale**2
)
full_tracker = TrackerCollection([body_tracker, eyes_tracker, tail_tracker])
tracker = full_tracker

tracker_display = TrackerDisp(name='tracking')

stimulus = Phototaxis(projector)

writer = CVWriter(
    height = camera_param.ROI_height,
    width = camera_param.ROI_width,
    fps = 100,
    filename = '/home/martin/Documents/tracking2.avi'
)

VirtualReality = VR(
    camera, 
    projector, 
    background, 
    cam2proj, 
    tracker, 
    tracker_display,
    stimulus,
    writer
)