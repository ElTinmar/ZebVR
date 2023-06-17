from core.dataclasses import CameraParameters
from devices.camera.dummycam import FromFile
from background.background import DynamicBackground
from tracking.body.body_tracker import BodyTracker
from tracking.eyes.eyes_tracker import EyesTracker
from tracking.tail.tail_tracker import TailTracker
import cv2

# TODO this should be part of camera calibration
cam_pixels_per_mm = 50
cam_mm_per_pixel = 1/cam_pixels_per_mm

camera_param = CameraParameters(
    ROI_height = 1088,
    ROI_width = 1088,
    fps = 120
)
camera = FromFile(
    video_file = 'toy_data/behavior_2000.avi',
    parameters = camera_param,
)

# background -------------------------------------------------
background = DynamicBackground(
    width = int(camera_param.ROI_width),
    height = int(camera_param.ROI_height),
    num_images = 200, 
    every_n_image = 2,
    rescale = 0.25
)

# trackers -------------------------------------------------
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
    arc_angle_deg = 150,
    n_pts_interp = 40,
    n_pts_arc = 20
)
polarity = -1
camera.start_acquisition()

cv2.namedWindow('eyes')
cv2.namedWindow('tail')
tracking_eyes = None
tracking_tail = None
for i in range(2000):
    data, keepgoing = camera.fetch()
    image = data.get_img()
    background.add_image(image)
    background_image = background.get_background()
    back_sub = polarity*(image - background_image)
    tracking = body_tracker.track(back_sub)
    if tracking is not None:
        tracking_eyes = eyes_tracker.track(back_sub, tracking.centroid, tracking.heading)
        tracking_tail = tail_tracker.track(back_sub, tracking.centroid, tracking.heading)

    if tracking_eyes is not None:
        cv2.imshow('eyes',tracking_eyes.image)
    if tracking_tail is not None:
        cv2.imshow('tail',tracking_tail.image)
    cv2.waitKey(1)

cv2.destroyAllWindows()