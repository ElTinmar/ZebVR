from devices.camera.dummycam import FromFile
from devices.projector.opencv_projector import CVProjector
from visual_stimuli.phototaxis import Phototaxis 
from background.background import DynamicBackground
from tracking.body.body_tracker import BodyTracker
from tracking.eyes.eyes_tracker import EyesTracker
from tracking.tail.tail_tracker import TailTracker
from tracking.prey.prey_tracker import PreyTracker
from tracking.tracker_collection import TrackerCollection 
from registration.registration_cam2proj import Cam2ProjReg
from parallel.dag import ZMQDataProcessingDAG
from core.dataclasses import CameraParameters
from core.VR_zmq import CameraZMQ, BackgroundZMQ, TrackerZMQ, StimulusZMQ, ProjectorZMQ

import time
import zmq

# camera -------------------------------------------------
camera_param = CameraParameters(
    ROI_height = 1088,
    ROI_width = 1088,
    fps = 10
)
camera = FromFile(
    video_file = 'toy_data/behavior_2000.avi',
    parameters = camera_param
)
camZMQ = CameraZMQ(camera = camera)

# background -------------------------------------------------
background = DynamicBackground(
    width = 1088,
    height = 1088,
    num_images = 200, 
    every_n_image = 2
)
backZMQ = BackgroundZMQ(background)

# trackers -------------------------------------------------
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
full_tracker = TrackerCollection([body_tracker, eyes_tracker, tail_tracker, prey_tracker])
#full_tracker = TrackerCollection([body_tracker])

tracker = full_tracker

trckzmq_0 = TrackerZMQ('Tracker0',tracker)
trckzmq_1 = TrackerZMQ('Tracker1',tracker)
trckzmq_2 = TrackerZMQ('Tracker2',tracker)

# projector --------------------------------------------------------
projector = CVProjector(monitor_id = 1)
projZMQ = ProjectorZMQ(projector)

# stimulus ---------------------------------------------------------
stimulus = Phototaxis(projector)
stimzmq = StimulusZMQ(stimulus)

# registration ---------------------------------------------------------
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

dag = [
    {
        'src': camZMQ,
        'dst': backZMQ,
        'protocol': 'tcp://',
        'address' : '127.0.0.1',
        'port': 5555,
        'send_flag': None,
        'recv_flag': None,
        'src_binds': True
    },
    {
        'src': backZMQ,
        'dst': trckzmq_0,
        'protocol': 'tcp://',
        'address' : '127.0.0.1',
        'port': 5556,
        'send_flag': None,
        'recv_flag': None,
        'src_binds': True
    },
    {
        'src': backZMQ,
        'dst': trckzmq_1,
        'protocol': 'tcp://',
        'address' : '127.0.0.1',
        'port': 5556,
        'send_flag': None,
        'recv_flag': None,
        'src_binds': True
    },
    {
        'src': backZMQ,
        'dst': trckzmq_2,
        'protocol': 'tcp://',
        'address' : '127.0.0.1',
        'port': 5556,
        'send_flag': None,
        'recv_flag': None,
        'src_binds': True
    },
    {
        'src': trckzmq_0,
        'dst': stimzmq,
        'protocol': 'tcp://',
        'address' : '127.0.0.1',
        'port': 5557,
        'send_flag': None,
        'recv_flag': None,
        'src_binds': False
    },
    {
        'src': trckzmq_1,
        'dst': stimzmq,
        'protocol': 'tcp://',
        'address' : '127.0.0.1',
        'port': 5557,
        'send_flag': None,
        'recv_flag': None,
        'src_binds': False
    },
    {
        'src': trckzmq_2,
        'dst': stimzmq,
        'protocol': 'tcp://',
        'address' : '127.0.0.1',
        'port': 5557,
        'send_flag': None,
        'recv_flag': None,
        'src_binds': False
    },
    {
        'src': stimzmq,
        'dst': projZMQ,
        'protocol': 'tcp://',
        'address' : '127.0.0.1',
        'port': 5558,
        'send_flag': None,
        'recv_flag': None,
        'src_binds': True
    }
]

"""
camera.calibration()
projector.calibration()
cam2proj.registration()
"""

VR = ZMQDataProcessingDAG(dag)
VR.start()

#time.sleep(120)
#VR.stop()
