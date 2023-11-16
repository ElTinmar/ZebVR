from camera_tools import Camera, MovieFileCam
from ZebVR import ZebVR_Worker, connect, receive_strategy, send_strategy
from tracker import (
    Tracker, LinearSumAssignment, 
    AnimalTracker, AnimalTrackerParamOverlay, AnimalTrackerParamTracking,
    BodyTracker, BodyTrackerParamOverlay, BodyTrackerParamTracking,
)
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
            tracking_param=AnimalTrackerParamTracking(
                animal_contrast=1.0,
                animal_gamma=1.0,
                animal_intensity=0.07,
                animal_norm=1.0,
                blur_sz_mm=0.13,
                max_animal_length_mm=12,
                max_animal_size_mm=30,
                max_animal_width_mm=2.5,
                median_filter_sz_mm=0.13,
                min_animal_length_mm=1,
                min_animal_size_mm=1,
                min_animal_width_mm=0.4,
                pad_value_mm=4,
                pix_per_mm=40,
                target_pix_per_mm=7.5
            )
        ),
        BodyTracker(
            overlay_param=BodyTrackerParamOverlay(),
            tracking_param=BodyTrackerParamTracking(
                pix_per_mm=40,
                target_pix_per_mm=7.5,
                body_intensity=0.06,
                body_gamma=3.0,
                body_contrast=1.5,
                body_norm=0.3,
                min_body_size_mm=2,
                max_body_size_mm=30,
                min_body_length_mm=2,
                max_body_length_mm=6,
                min_body_width_mm=0.4,
                max_body_width_mm=1.2,
                blur_sz_mm=0.13,
                median_filter_sz_mm=0.13
            )
        ),
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