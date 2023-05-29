from .protocols import Camera, Projector, Background, Cam2Proj, Tracker, Stimulus
from parallel.dag import ZMQDataProcessingDAG, ZMQDataProcessingNode, DataInfo
import time
import zmq

camera = None
background = None
tracker_0 = None
tracker_1 = None
tracker_2 = None
overlay = None
stimulus = None
projector = None
cam2proj = None

dag = [
    {
        'src': camera,
        'dst': background,
        'port': 5555,
        'send_flag': zmq.NOBLOCK,
        'recv_flag': None
    },
    {
        'src': background,
        'dst': tracker_0,
        'port': 5556,
        'send_flag': zmq.NOBLOCK,
        'recv_flag': None
    },
    {
        'src': background,
        'dst': tracker_1,
        'port': 5556,
        'send_flag': zmq.NOBLOCK,
        'recv_flag': None
    },
    {
        'src': background,
        'dst': tracker_2,
        'port': 5556,
        'send_flag': zmq.NOBLOCK,
        'recv_flag': None
    },
    {
        'src': tracker_0,
        'dst': overlay,
        'port': 5557,
        'send_flag': zmq.NOBLOCK,
        'recv_flag': None
    },
    {
        'src': tracker_1,
        'dst': overlay,
        'port': 5557,
        'send_flag': zmq.NOBLOCK,
        'recv_flag': None
    },
    {
        'src': tracker_2,
        'dst': overlay,
        'port': 5557,
        'send_flag': zmq.NOBLOCK,
        'recv_flag': None
    },
    {
        'src': tracker_0,
        'dst': stimulus,
        'port': 5558,
        'send_flag': zmq.NOBLOCK,
        'recv_flag': None
    },
    {
        'src': tracker_1,
        'dst': stimulus,
        'port': 5558,
        'send_flag': zmq.NOBLOCK,
        'recv_flag': None
    },
    {
        'src': tracker_2,
        'dst': stimulus,
        'port': 5558,
        'send_flag': zmq.NOBLOCK,
        'recv_flag': None
    },
    {
        'src': stimulus,
        'dst': projector,
        'port': 5559,
        'send_flag': zmq.NOBLOCK,
        'recv_flag': None
    }
]

camera.calibration()
projector.calibration()
cam2proj.registration()

VR = ZMQDataProcessingDAG(dag)
VR.start()
time.sleep(120)
VR.stop()
