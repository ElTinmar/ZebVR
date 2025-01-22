from dagline import ProcessingDAG, receive_strategy, send_strategy, WorkerNode
from ipc_tools import ModifiableRingBuffer, MonitoredQueue
from multiprocessing_logger import Logger
from ZebVR.workers import Display, CameraWorker
import numpy as np
from numpy.typing import NDArray
import time
from typing import Any, Tuple
from PyQt5.QtWidgets import QApplication
from ZebVR.widgets import DisplayWidget
from camera_tools import OpenCV_Webcam
try:
    from camera_tools import XimeaCamera
    XIMEA_ENABLED = True
except ImportError:
    XIMEA_ENABLED = False

worker_logger = Logger('worker.log', Logger.INFO)
queue_logger = Logger('queue.log', Logger.INFO)

class Thresholder(WorkerNode):

    def __init__(
            self, 
            threshold: int = 200,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.threshold = threshold

    def process_data(self, data: None): 

        if data is None:
            return None
    
        img = data['image']
        detected = False
        avg = np.mean(img)
        print(avg)
        if avg >= self.threshold:
            detected = True

        res = np.array(
            (data['index'], data['timestamp'], detected),
            dtype=np.dtype([
                ('index', int),
                ('timestamp', np.float64),
                ('detected', np.bool_)
            ])
        )
        
        return res
        
    def process_metadata(self, metadata) -> Any:
        pass

class Flash(WorkerNode):

    def __init__(
            self, 
            pos: Tuple[int,int] = (0,0),
            resolution: Tuple[int,int] = (512,512),
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.pos = pos
        self.resolution = resolution 
        self.white = 255*np.ones(resolution, dtype=np.uint8)
        self.black = np.zeros(resolution, dtype=np.uint8)

    def initialize(self) -> None:

        super().initialize()
        
        self.app = QApplication([])
        self.window = DisplayWidget(display_height=self.resolution[0])
        self.window.set_state(
            index = -1,
            timestamp = -1,
            image_rgb = self.black
        )
        self.window.setGeometry(
            self.pos[0],
            self.pos[1],
            self.resolution[0],
            self.resolution[1]
        )
        self.window.show()

    def process_data(self, data) -> NDArray:
        
        if data is None:
            time.sleep(0.001)
            return

        if data['detected']:
            self.window.set_state(
                index = data['index'],
                timestamp = data['timestamp'],
                image_rgb = self.white
            )

        #else:
            #self.window.set_state(
            #    index = data['index'],
            #    timestamp = data['timestamp'],
            #    image_rgb = self.black
            #)
        
        self.app.processEvents()
        self.app.sendPostedEvents()
        print(f"latency {1e-6*(time.perf_counter_ns() - data['timestamp'])}")


    def process_metadata(self, metadata) -> Any:
        pass
        
camera = CameraWorker(
    camera_constructor = XimeaCamera, 
    exposure = 1000,
    gain = 0,
    framerate = 170,
    height = 2048,
    width = 2048,
    offsetx = 0,
    offsety = 0,
    name = 'camera', 
    logger = worker_logger, 
    logger_queues = queue_logger,
    receive_data_strategy = receive_strategy.COLLECT, 
    send_data_strategy = send_strategy.BROADCAST, 
    receive_data_timeout = 1.0,
    profile = False
)

thresholder = Thresholder(
    threshold = 2.7,
    name = 'thresholder', 
    logger = worker_logger, 
    logger_queues = queue_logger,
)

flash = Flash(
    pos = (1920,0),
    resolution = (1080,1920),
    name = 'flash', 
    logger = worker_logger, 
    logger_queues = queue_logger,
)

queue1 = MonitoredQueue(
    ModifiableRingBuffer(
    num_bytes = 500*1024**2,
    logger = queue_logger,
    name = 'camera_to_thresholder'
)
)
queue2 = MonitoredQueue(
    ModifiableRingBuffer(
    num_bytes = 500*1024**2,
    logger = queue_logger,
    name = 'thresholder_to_display'
)
)

dag = ProcessingDAG()

dag.connect_data(
    sender = camera, 
    receiver = thresholder, 
    queue = queue1, 
    name = 'cam_output1'
)

dag.connect_data(
    sender = thresholder, 
    receiver = flash, 
    queue = queue2, 
    name = 'threshold_out0'
)

dag.start()
time.sleep(10)
dag.stop()

print('cam to thresh', queue1.get_average_freq(), queue1.queue.num_lost_item.value)
print('thresh to flash', queue2.get_average_freq(), queue2.queue.num_lost_item.value)
