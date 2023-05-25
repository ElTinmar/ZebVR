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

body_tracker = BodyTracker()
eyes_tracker = EyesTracker()
tail_tracker = TailTracker()
prey_tracker = PreyTracker()
full_tracker = TrackerCollection([eyes_tracker, tail_tracker, prey_tracker])

tracker = full_tracker

stimulus = 

VirtualReality = VR(camera, projector, background, cam2proj, tracker, stimulus)