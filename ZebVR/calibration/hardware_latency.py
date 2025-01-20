from dagline import ProcessingDAG, receive_strategy, send_strategy, WorkerNode
from ipc_tools import ModifiableRingBuffer
from multiprocessing_logger import Logger
from ZebVR.workers import Display, CameraWorker
from camera_tools import OpenCV_Webcam
import numpy as np
from numpy.typing import NDArray
import time
from typing import Any
from PyQt5.QtWidgets import QApplication
from ZebVR.widgets import DisplayWidget

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
        if np.mean(img) >= self.threshold:
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
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.white = 255*np.ones((1024,1024), dtype=np.uint8)
        self.black = np.zeros((1024,1024), dtype=np.uint8)

    def initialize(self) -> None:

        super().initialize()
        
        self.app = QApplication([])
        self.window = DisplayWidget()
        self.window.set_state(
            index = -1,
            timestamp = -1,
            image_rgb = self.black
        )
        self.window.show()

    def process_data(self, data) -> NDArray:

        self.app.processEvents()
        self.app.sendPostedEvents()
        
        if data is None:
            time.sleep(0.001)
            return

        if data['detected']:
            self.window.set_state(
                index = data['index'],
                timestamp = data['timestamp'],
                image_rgb = self.white
            )
            print(f"latency {1e-6*(time.perf_counter_ns() - data['timestamp'])}")

    def process_metadata(self, metadata) -> Any:
        pass
        
camera = CameraWorker(
    camera_constructor = OpenCV_Webcam, 
    exposure = 0,
    gain = 0,
    framerate = 30,
    height = 480,
    width = 640,
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
    threshold = 200,
    name = 'thresholder', 
    logger = worker_logger, 
    logger_queues = queue_logger,
)

flash = Flash(
    name = 'flash', 
    logger = worker_logger, 
    logger_queues = queue_logger,
)

queue1 = ModifiableRingBuffer(
    num_bytes = 500*1024**2,
    logger = queue_logger,
    name = 'camera_to_thresholder'
)
queue2 = ModifiableRingBuffer(
    num_bytes = 500*1024**2,
    logger = queue_logger,
    name = 'thresholder_to_display'
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
time.sleep(20)
dag.stop()