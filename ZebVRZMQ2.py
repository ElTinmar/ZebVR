from devices.camera.dummycam import FromFile
from devices.camera.display import CamDisp
from devices.projector.opencv_projector import CVProjector
from visual_stimuli.phototaxis import Phototaxis 
from background.background import DynamicBackground
from tracking.body.body_tracker import BodyTrackerPCA
from tracking.eyes.eyes_tracker import EyesTracker
from tracking.tail.tail_tracker import TailTracker
from tracking.prey.prey_tracker import PreyTracker
from tracking.tracker_collection import TrackerCollection 
from registration.registration_cam2proj import Cam2ProjReg
from parallel.zmq_worker import ZMQSocketInfo
from parallel.serialization import send_frame, recv_frame, send_tracking, recv_tracking
from core.dataclasses import CameraParameters
from tracking.display import TrackerDisp
from core.VR_zmq import CameraZMQ, BackgroundZMQ, TrackerZMQ, StimulusZMQ, ProjectorZMQ, CameraDisplayZMQ, TrackerDisplayZMQ
import zmq

# camera -------------------------------------------------
rescale = 0.25

# TODO this should be part of camera calibration
cam_pixels_per_mm = 50
cam_mm_per_pixel = 1/cam_pixels_per_mm

camera_param = CameraParameters(
    ROI_height = 2048,
    ROI_width = 2048,
    fps = 10
)
camera = FromFile(
    video_file = 'toy_data/50mm2_mjpeg.avi',
    parameters = camera_param,
    rescale = rescale
)

# camera display ------------------------------------------
cam_display = CamDisp('camera')

# background -------------------------------------------------
background = DynamicBackground(
    width = int(camera_param.ROI_width*rescale),
    height = int(camera_param.ROI_height*rescale),
    num_images = 200, 
    every_n_image = 2
)

# trackers -------------------------------------------------
body_tracker = BodyTrackerPCA(
    threshold_body_intensity = 0.2,
    threshold_body_area = 10 * cam_pixels_per_mm * rescale**2,
    width = int(camera_param.ROI_width*rescale),
    height = int(camera_param.ROI_height*rescale),
    dynamic_cropping_len = int(5 * cam_pixels_per_mm)
)
eyes_tracker = EyesTracker(
    threshold_body_intensity = 0.2,
    threshold_body_area = 10 * cam_pixels_per_mm * rescale**2,
    width = int(camera_param.ROI_width*rescale),
    height = int(camera_param.ROI_height*rescale),
    dynamic_cropping_len = int(5 * cam_pixels_per_mm),
    threshold_eye_intensity = 0.4,
    threshold_eye_area_min = 2 * cam_pixels_per_mm * rescale**2,
    threshold_eye_area_max = 10 * cam_pixels_per_mm * rescale**2,
    dist_eye_midline = 0.1 * cam_pixels_per_mm * rescale,
    dist_eye_swimbladder = 0.2 * cam_pixels_per_mm * rescale
)
tail_tracker = TailTracker(
    threshold_body_intensity = 0.2,
    threshold_body_area = 10 * cam_pixels_per_mm * rescale**2,
    width = int(camera_param.ROI_width*rescale),
    height = int(camera_param.ROI_height*rescale),
    dynamic_cropping_len = int(5 * cam_pixels_per_mm),
    tail_length = 3 * cam_pixels_per_mm * rescale,
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
full_tracker = TrackerCollection([body_tracker, eyes_tracker, tail_tracker, prey_tracker])
full_tracker = TrackerCollection([body_tracker])
tracker = full_tracker

# tracker disp ----------------------------------------------------
tracker_display = TrackerDisp(
    name='tracking',
    alpha = 2.0 * cam_pixels_per_mm * rescale,
    beta = 0.2 * cam_pixels_per_mm * rescale,
    circle_radius = int(0.4 * cam_pixels_per_mm * rescale)
)

# projector --------------------------------------------------------
projector = CVProjector(monitor_id = 1)

# stimulus ---------------------------------------------------------
stimulus = Phototaxis(projector)

# registration -----------------------------------------------------
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

# Processing DAG ----------------------------------------------------
base_port = 8010

cam_out0 = ZMQSocketInfo(
    port = base_port,
    socket_type = zmq.PUSH,
    bind = True,
    serializer = send_frame
)

cam_out1 = ZMQSocketInfo(
    port = base_port+1,
    socket_type = zmq.PUSH,
    bind = True,
    serializer = send_frame
)

cam_disp_in = ZMQSocketInfo(
    port = cam_out1.port,
    socket_type = zmq.PULL,
    deserializer = recv_frame
)

bckg_in = ZMQSocketInfo(
    port = cam_out0.port,
    socket_type = zmq.PULL,
    deserializer = recv_frame
)

bckg_out = ZMQSocketInfo(
    port = base_port+2,
    socket_type = zmq.PUSH,
    bind = True,
    serializer = send_frame
)

tracker0_in = ZMQSocketInfo(
    port = bckg_out.port,
    socket_type = zmq.PULL,
    deserializer = recv_frame
)

tracker0_out = ZMQSocketInfo(
    port = base_port+3,
    socket_type = zmq.PUSH,
    bind = True,
    serializer = send_tracking
)

tracker0_out1 = ZMQSocketInfo(
    port = base_port+4,
    socket_type = zmq.PUSH,
    bind = True,
    serializer = send_tracking
)

tracker1_in = ZMQSocketInfo(
    port = bckg_out.port,
    socket_type = zmq.PULL,
    deserializer = recv_frame
)

tracker1_out = ZMQSocketInfo(
    port = base_port+5,
    socket_type = zmq.PUSH,
    bind = True,
    serializer = send_tracking
)

tracker1_out1 = ZMQSocketInfo(
    port = base_port+6,
    socket_type = zmq.PUSH,
    bind = True,
    serializer = send_tracking
)

tracker2_in = ZMQSocketInfo(
    port = bckg_out.port,
    socket_type = zmq.PULL,
    deserializer = recv_frame
)

tracker2_out = ZMQSocketInfo(
    port = base_port+7,
    socket_type = zmq.PUSH,
    bind = True,
    serializer = send_tracking
)

tracker2_out1 = ZMQSocketInfo(
    port = base_port+8,
    socket_type = zmq.PUSH,
    bind = True,
    serializer = send_tracking
)

tracker_disp_in0 = ZMQSocketInfo(
    port = tracker0_out1.port,
    socket_type = zmq.PULL,
    deserializer = recv_tracking
)

tracker_disp_in1 = ZMQSocketInfo(
    port = tracker1_out1.port,
    socket_type = zmq.PULL,
    deserializer = recv_tracking
)

tracker_disp_in2 = ZMQSocketInfo(
    port = tracker2_out1.port,
    socket_type = zmq.PULL,
    deserializer = recv_tracking
)

stim0_in = ZMQSocketInfo(
    port = tracker0_out.port,
    socket_type = zmq.PULL,
    deserializer = recv_tracking
)

stim0_out = ZMQSocketInfo(
    port = base_port+9,
    socket_type = zmq.PUSH,
    bind = True,
    serializer = send_frame
)

stim1_in = ZMQSocketInfo(
    port = tracker1_out.port,
    socket_type = zmq.PULL,
    deserializer = recv_tracking
)

stim1_out = ZMQSocketInfo(
    port = base_port+10,
    socket_type = zmq.PUSH,
    bind = True,
    serializer = send_frame
)

stim2_in = ZMQSocketInfo(
    port = tracker2_out.port,
    socket_type = zmq.PULL,
    deserializer = recv_tracking
)

stim2_out = ZMQSocketInfo(
    port = base_port+11,
    socket_type = zmq.PUSH,
    bind = True,
    serializer = send_frame
)

projector_in0 = ZMQSocketInfo(
    port = stim0_out.port,
    socket_type = zmq.PULL,
    deserializer = recv_frame
)

projector_in1 = ZMQSocketInfo(
    port = stim1_out.port,
    socket_type = zmq.PULL,
    deserializer = recv_frame
)

projector_in2 = ZMQSocketInfo(
    port = stim2_out.port,
    socket_type = zmq.PULL,
    deserializer = recv_frame
)

# create and start nodes -------------------------------------------
camZMQ = CameraZMQ(
    camera = camera,
    input_info = [],
    output_info = [cam_out0,cam_out1]
)

camdispZMQ = CameraDisplayZMQ(
    cam_display,
    input_info=[cam_disp_in],
    output_info=[]
    )

backZMQ = BackgroundZMQ(
    background,
    input_info = [bckg_in],
    output_info = [bckg_out]
)

trckzmq_0 = TrackerZMQ(
    'Tracker0',
    tracker,
    input_info = [tracker0_in],
    output_info = [tracker0_out, tracker0_out1]
)

trckzmq_1 = TrackerZMQ(
    'Tracker1',
    tracker,
    input_info = [tracker1_in],
    output_info = [tracker1_out, tracker1_out1]
)

trckzmq_2 = TrackerZMQ(
    'Tracker2',
    tracker,
    input_info = [tracker2_in],
    output_info = [tracker2_out, tracker2_out1]
)

trckdisp = TrackerDisplayZMQ(
    tracker_display,
    input_info=[tracker_disp_in0, tracker_disp_in1, tracker_disp_in2],
    output_info=[]
)

stimzmq_0 = StimulusZMQ(
    stimulus,
    input_info = [stim0_in],
    output_info = [stim0_out],
    name = 'stim0'
)

stimzmq_1 = StimulusZMQ(
    stimulus,
    input_info = [stim1_in],
    output_info = [stim1_out],
    name = 'stim1'
)

stimzmq_2 = StimulusZMQ(
    stimulus,
    input_info = [stim2_in],
    output_info = [stim2_out],
    name = 'stim2'
)

projZMQ = ProjectorZMQ(
    projector,
    input_info = [projector_in0, projector_in1, projector_in2],
    output_info = []
)

projZMQ.start()
stimzmq_2.start()
stimzmq_1.start()
stimzmq_0.start()
trckdisp.start()
trckzmq_2.start()
trckzmq_1.start()
trckzmq_0.start()
backZMQ.start()
camdispZMQ.start()
camZMQ.start()

"""
camera.calibration()
projector.calibration()
cam2proj.registration()
"""

#time.sleep(120)
#VR.stop()
