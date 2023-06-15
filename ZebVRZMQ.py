from devices.camera.dummycam import FromFile
from devices.camera.display import CamDisp
from devices.projector.opencv_projector import CVProjector
from visual_stimuli.phototaxis import Phototaxis 
from background.background import DynamicBackground
from tracking.body.body_tracker import BodyTracker
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
import multiprocessing

if __name__ == '__main__':

    multiprocessing.set_start_method('spawn')

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
        parameters = camera_param,
    )

    # camera display ------------------------------------------
    cam_display = CamDisp('camera',rescale=0.25)

    # background -------------------------------------------------
    background = DynamicBackground(
        width = int(camera_param.ROI_width),
        height = int(camera_param.ROI_height),
        num_images = 200, 
        every_n_image = 2,
        rescale=0.25
    )

    # trackers -------------------------------------------------
    body_tracker = BodyTracker(
        threshold_body_intensity = 0.2,
        dynamic_cropping_len_mm = 5,
        pixels_per_mm = cam_pixels_per_mm,
        rescale = 0.25
    )
    eyes_tracker = EyesTracker(
        body_tracker = body_tracker,
        pixels_per_mm = cam_pixels_per_mm,
        dynamic_cropping_len_mm = 5,
        threshold_eye_intensity = 0.4,
        rescale = 0.25
    )
    tail_tracker = TailTracker(
        body_tracker = body_tracker,
        dynamic_cropping_len_mm = 5,
        pixels_per_mm = cam_pixels_per_mm,
        n_tail_points = 12,
        ksize = 5,
        arc_angle_deg = 150,
        n_pts_interp = 40,
        n_pts_arc = 20,
        rescale = 0.25
    )
    prey_tracker = PreyTracker(
        threshold_prey_intensity = 0.025,
        pixels_per_mm = cam_pixels_per_mm,
        rescale = 0.25
    )
    #full_tracker = TrackerCollection([body_tracker, eyes_tracker, tail_tracker, prey_tracker])
    full_tracker = TrackerCollection([body_tracker, eyes_tracker, tail_tracker])
    tracker = full_tracker

    # tracker disp ----------------------------------------------------
    tracker_display = TrackerDisp(
        name='tracking',
        pixels_per_mm = cam_pixels_per_mm,
        rescale = 0.25
    )

    # projector --------------------------------------------------------
    projector = CVProjector(monitor_id = 1)

    # stimulus ---------------------------------------------------------
    stimulus = Phototaxis(screenid=1)

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
    base_port = 8000

    cam_out0 = ZMQSocketInfo(
        port = base_port,
        socket_type = zmq.PUSH,
        bind = True,
        serializer = send_frame
    )

    cam_out1 = ZMQSocketInfo(
        port = base_port + 1,
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
        port = base_port + 2,
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
        port = base_port + 3,
        socket_type = zmq.PUSH,
        bind = True,
        serializer = send_tracking
    )

    tracker0_out1 = ZMQSocketInfo(
        port = base_port + 4,
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
        port = base_port + 5,
        socket_type = zmq.PUSH,
        bind = True,
        serializer = send_tracking
    )

    tracker1_out1 = ZMQSocketInfo(
        port = base_port + 6,
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
        port = base_port + 7,
        socket_type = zmq.PUSH,
        bind = True,
        serializer = send_tracking
    )

    tracker2_out1 = ZMQSocketInfo(
        port = base_port + 8,
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

    stim_in0 = ZMQSocketInfo(
        port = tracker0_out.port,
        socket_type = zmq.PULL,
        deserializer = recv_tracking
    )
    stim_in1 = ZMQSocketInfo(
        port = tracker1_out.port,
        socket_type = zmq.PULL,
        deserializer = recv_tracking
    )
    stim_in2 = ZMQSocketInfo(
        port = tracker2_out.port,
        socket_type = zmq.PULL,
        deserializer = recv_tracking
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

    stimzmq = StimulusZMQ(
        stimulus,
        input_info = [stim_in0,stim_in1,stim_in2],
        output_info = [],
        name = 'stim0'
    )

    stimzmq.start()
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
