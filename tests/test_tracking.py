from camera_tools import Camera, MovieFileCam
from ZebVR import ZebVR_Worker, connect, receive_strategy, send_strategy
from tracker import Tracker, AnimalTracker, LinearSumAssignment, AnimalTrackerParamOverlay, AnimalTrackerParamTracking
from multiprocessing_logger import Logger
from ipc_tools import RingBuffer, QueueMP, ZMQ_PushPullArray, MonitoredQueue
import numpy as np
import time
from video_tools import BackgroundSubtractor, BackroundImage, Polarity
from image_tools import im2single, im2gray

class CameraWorker(ZebVR_Worker):

    def __init__(self, cam: Camera, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cam = cam

    def initialize(self) -> None:
        super().initialize()
        self.cam.start_acquisition()

    def cleanup(self) -> None:
        super().cleanup()
        self.cam.stop_acquisition()
    
    def work(self, data):
        return self.cam.get_frame().image
    
class BackgroundSubWorker(ZebVR_Worker):

    def __init__(self, sub: BackgroundSubtractor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sub = sub

    def initialize(self) -> None:
        super().initialize()
        self.sub.initialize()

    def work(self, data):
        image = im2single(im2gray(data))
        return self.sub.subtract_background(image)
         
class TrackerWorker(ZebVR_Worker):
    
    def __init__(self, tracker: Tracker, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tracker = tracker

    def work(self, data):
        tracking = self.tracker.track(data)
        return tracking['animals'].centroids
    
class Printer(ZebVR_Worker):

    def work(self, data):
        print(data)

if __name__ == "__main__":

    m = MovieFileCam(filename='toy_data/19-40-44.avi')
    t = Tracker(
        LinearSumAssignment(10), 
        None, 
        AnimalTracker(
            overlay_param=AnimalTrackerParamOverlay(),
            tracking_param=AnimalTrackerParamTracking()
        ),
        None,
        None,
        None
    )
    l = Logger('test_tracking.log', Logger.DEBUG)
    b = BackroundImage(
        image_file_name = 'toy_data/19-40-44.png',
        polarity = Polarity.DARK_ON_BRIGHT
    )

    h, w = (m.get_height(), m.get_width())

    cam = CameraWorker(cam = m, name='camera', logger = l)
    trck = TrackerWorker(t, name='tracker', logger = l)
    prt = Printer(name='printer', logger = l)
    bckg = BackgroundSubWorker(b, name='background', logger = l)

    q_cam = MonitoredQueue(
        RingBuffer(
            num_items = 100,
            item_shape = (h, w, 3),
            data_type = np.uint8
        )
    )
    q_back = MonitoredQueue(
        RingBuffer(
            num_items = 100,
            item_shape = (h, w),
            data_type = np.float32
        )
    )
    q_tracking = MonitoredQueue(QueueMP())

    connect(sender=cam, receiver=bckg, queue=q_cam)
    connect(sender=bckg, receiver=trck, queue=q_back)
    connect(sender=trck, receiver=prt, queue=q_tracking)

    l.start()
    prt.start()
    trck.start()
    bckg.start()
    cam.start()

    time.sleep(10)

    cam.stop()
    bckg.stop()
    trck.stop()
    prt.stop()
    l.stop()

    print(q_cam.get_average_freq())
    print(q_back.get_average_freq())
    print(q_tracking.get_average_freq())