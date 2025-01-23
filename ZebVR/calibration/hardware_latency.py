from dagline import ProcessingDAG, receive_strategy, send_strategy, WorkerNode
from ipc_tools import ModifiableRingBuffer, MonitoredQueue
from multiprocessing_logger import Logger
from ZebVR.workers import CameraWorker
from ZebVR.stimulus import VisualStim, VisualStimWorker
from vispy import app, gloo
from multiprocessing import Value
import numpy as np
from numpy.typing import NDArray
import time
from typing import Any, Tuple
from camera_tools import OpenCV_Webcam
try:
    from camera_tools import XimeaCamera
    XIMEA_ENABLED = True
    constructor = XimeaCamera
except ImportError:
    XIMEA_ENABLED = False
    constructor = OpenCV_Webcam

worker_logger = Logger('worker.log', Logger.INFO)
queue_logger = Logger('queue.log', Logger.INFO)

# Estimation of hardware timings
# ------------------------------ 
#   XIMEA camera readout: 
#       2048x2048, 1ms exposure time, PCIe Gen2X2 limited at 727MBps: 
#       ~5.7ms readout + 1ms exposure = ~6.7ms total 
#
#   Processing:
#       ~3ms
#
#   Compositor:
#       Double-buffering @240Hz: 4.2ms
#   
#   ViewSonic X2-4K projector: 
#       1920x1080 @ 240Hz, 4.2ms input lag over HDMI 2.0 (18 Gbps). 
#       Data transmission assuming RGB ~2.7ms + 4.2ms to display = 6.9ms total
#
# Total: 5.7 + 3 + 4.2 + 6.9 = ~20ms 


class Thresholder(WorkerNode):

    def __init__(
            self, 
            threshold: int = 200,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.threshold = threshold

    def process_data(self, data: Any): 

        if data is None:
            return None
    
        img = data['image']
        detected = False
        avg = np.mean(img)
        #print(avg)
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


VERT_SHADER = """
attribute vec2 a_position;
uniform mat3 u_transformation_matrix;
uniform float u_pix_per_mm; 

void main()
{
    gl_Position = vec4(a_position, 0.0, 1.0);
}
"""

FRAG_SHADER = """
uniform float on;
uniform vec2 u_pixel_scaling; 
uniform float u_time;

void main()
{
    gl_FragColor = vec4(0.0,0.0,0.0,1.0);

    if (on == 1) {
        gl_FragColor = vec4(1.0,1.0,1.0,1.0);
    }
}
"""

class Flash2(VisualStim):

    def __init__(
            self,  
            window_size: Tuple[int, int], 
            window_position: Tuple[int, int], 
            window_decoration: bool = False,
            transformation_matrix: NDArray = np.eye(3, dtype=np.float32),
            pixel_scaling: Tuple[float, float] = (1.0,1.0),
            pix_per_mm: float = 30,
            refresh_rate: int = 240,
            vsync: bool = False,
            double_buffering: bool = True,
        ) -> None:

        super().__init__(
            vertex_shader=VERT_SHADER, 
            fragment_shader=FRAG_SHADER, 
            window_size=window_size,
            window_position=window_position, 
            pix_per_mm=pix_per_mm, 
            window_decoration=window_decoration, 
            transformation_matrix=transformation_matrix, 
            pixel_scaling=pixel_scaling, 
            vsync=vsync,
            double_buffering=double_buffering
        )

        self.on = Value('d',0)
        self.timestamp = Value('d',0)
        self.refresh_rate = refresh_rate

    def initialize(self):
        super().initialize()
        self.program['on'] = 0.0
        self.timer = app.Timer(1/self.refresh_rate, self.on_timer)
        self.timer.start()
        self.show()

    def on_timer(self, event):
        self.program['on'] = self.on.value
        self.update()
        if self.on.value:
            print(f"latency {1e-6*(time.perf_counter_ns() - self.timestamp.value)}, detected: {self.on.value}")

    def on_draw(self, event):
        super().on_draw(event)
        gloo.clear('black')
        self.program.draw('triangle_strip')

    def process_data(self, data) -> None:
        if data is not None:
            self.on.value = data['detected']
            self.timestamp.value = data['timestamp']

    def process_metadata(self, metadata) -> None:
        pass
        
camera = CameraWorker(
    camera_constructor = constructor, 
    exposure = 1000,
    gain = 0,
    framerate = 100,
    height = 2048,
    width = 2048,
    offsetx = 0,
    offsety = 0,
    name = 'camera', 
    logger = worker_logger, 
    logger_queues = queue_logger,
    receive_data_strategy = receive_strategy.COLLECT, 
    send_data_strategy = send_strategy.BROADCAST, 
)

thresholder = Thresholder(
    threshold = 2.6,
    name = 'thresholder', 
    logger = worker_logger, 
    logger_queues = queue_logger,
)

flash_stim = Flash2(
    window_position = (1920,0),
    window_size = (1920,1080),
)

flash_worker = VisualStimWorker(
    stim = flash_stim, 
    name = 'flash', 
    logger = worker_logger, 
    logger_queues = queue_logger
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
    receiver = flash_worker, 
    queue = queue2, 
    name = 'threshold_out0'
)

dag.start()
time.sleep(120)
dag.stop()

print('cam to thresh', queue1.get_average_freq(), queue1.queue.num_lost_item.value)
print('thresh to flash', queue2.get_average_freq(), queue2.queue.num_lost_item.value)
