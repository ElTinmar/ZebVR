from devices.camera.ximea import XimeaCamera
from devices.camera.display import CamDisp
from parallel.zmq_worker import ZMQSocketInfo
from parallel.serialization import send_frame, recv_frame
from core.dataclasses import CameraParameters
from core.VR_zmq import CameraZMQ,CameraDisplayZMQ
import zmq
import multiprocessing

if __name__ == '__main__':

    # make sure multiprocessing is compatible with windows
    multiprocessing.set_start_method('spawn')

    # TODO this should be part of camera calibration
    cam_pixels_per_mm = 50
    cam_mm_per_pixel = 1/cam_pixels_per_mm

    camera_param = CameraParameters(
        exposure_time_ms = 1000,
        fps = 200,
        ROI_height = 1088,
        ROI_width = 1088,
        gain = 4.0,
        ROI_left = 0,
        ROI_top = 0
    )
    camera = XimeaCamera(
        parameters = camera_param,
    )
    
    # camera display ------------------------------------------
    cam_display = CamDisp('camera', rescale=0.25)

    # Processing DAG ----------------------------------------------------
    base_port = 8000

    cam_out = ZMQSocketInfo(
        port = base_port ,
        socket_type = zmq.PUSH,
        bind = True,
        serializer = send_frame
    )
    cam_disp_in = ZMQSocketInfo(
        port = cam_out.port,
        socket_type = zmq.PULL,
        deserializer = recv_frame
    )

    # create and start nodes -------------------------------------------
    camZMQ = CameraZMQ(
        camera = camera,
        input_info = [],
        output_info = [cam_out]
    )

    camdispZMQ = CameraDisplayZMQ(
        cam_display,
        input_info=[cam_disp_in],
        output_info=[]
        )

    camdispZMQ.start()
    camZMQ.start()

