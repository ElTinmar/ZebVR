from core.VR import VR
from devices.camera.dummycam import FromFile, RandomCam
from devices.projector.opencv_projector import CVProjector
from background.background import Background
from tracking.body.body_tracker import BodyTracker
from tracking.eyes.eyes_tracker import EyesTracker
from tracking.tail.tail_tracker import TailTracker
from tracking.prey.prey_tracker import PreyTracker
from tracking.tracker_collection import TrackerCollection 

cam_opts = {"ROI_height": 128, "ROI_width": 256}
camera = RandomCam(**cam_opts)

projector = CVProjector(monitor_id = 1)

background = Background(num_images = 500, every_n_image = 100)

cam2proj = 

body_tracker = BodyTracker(
    threshold_body_intensity = 0.2,
    threshold_body_area = 500
)
eyes_tracker = EyesTracker(
    threshold_body_intensity = 0.2,
    threshold_body_area = 500,
    threshold_eye_intensity = 0.4,
    threshold_eye_area_min = 100,
    threshold_eye_area_max = 500
)
tail_tracker = TailTracker(
    threshold_body_intensity = 0.2,
    threshold_body_area = 500,
    tail_length = 160,
    n_tail_points = 12,
    ksize = 5,
    arc_angle_deg = 150,
    n_pts_interp = 40,
    n_pts_arc = 20
)
prey_tracker = PreyTracker(
    threshold_prey_intensity = 0.025,
    threshold_prey_area_min = 15,
    threshold_prey_area_max = 100
)
full_tracker = TrackerCollection([eyes_tracker, tail_tracker, prey_tracker])
tracker = full_tracker

stimulus = 

VirtualReality = VR(camera, projector, background, cam2proj, tracker, stimulus)