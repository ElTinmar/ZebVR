from camera_tools import Camera, MovieFileCam
from ZebVR import ZebVR_Worker, connect, receive_strategy, send_strategy
from tracker import (
    Tracker, LinearSumAssignment, 
    AnimalTracker, AnimalTrackerParamOverlay, AnimalTrackerParamTracking,
    BodyTracker, BodyTrackerParamOverlay, BodyTrackerParamTracking,
    TailTracker, TailTrackerParamOverlay, TailTrackerParamTracking,
    EyesTracker, EyesTrackerParamOverlay, EyesTrackerParamTracking
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
        self.prev_time = 0

    def initialize(self) -> None:
        super().initialize()
        self.cam.start_acquisition()

    def cleanup(self) -> None:
        super().cleanup()
        self.cam.stop_acquisition()
    
    def work(self, data):
        res = self.cam.get_frame().image
        elapsed = (time.monotonic_ns() - self.prev_time) * 1e-6
        while elapsed < 1000/200:
            time.sleep(0.001)
            elapsed = (time.monotonic_ns() - self.prev_time) * 1e-6
        self.prev_time = time.monotonic_ns()
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
        EyesTracker(
            overlay_param=EyesTrackerParamOverlay(),
            tracking_param=EyesTrackerParamTracking(
                pix_per_mm=40,
                target_pix_per_mm=40,
                eye_gamma=2.5,
                eye_contrast=0.4,
                eye_norm=0.3,
                eye_dyntresh_res=5,
                eye_size_lo_mm=0.8,
                eye_size_hi_mm=10,
                crop_dimension_mm=(1.0,1,5),
                crop_offset_mm=-0.3,
                blur_sz_mm=0.06,
                median_filter_sz_mm=0.06
            )
        ),
        TailTracker(
            overlay_param=TailTrackerParamOverlay(),
            tracking_param=TailTrackerParamTracking(
                pix_per_mm=40,
                target_pix_per_mm=20,
                tail_contrast=1,
                tail_gamma=0.75,
                tail_norm=0.2,
                arc_angle_deg=120,
                n_tail_points=12,
                n_pts_arc=20,
                n_pts_interp=40,
                tail_length_mm=2.6,
                crop_offset_tail_mm=2.25,
                dist_swim_bladder_mm=0.2,
                crop_dimension_mm=(3.5,3.5),
                blur_sz_mm=0.06,
                median_filter_sz_mm=0.06
            )
        )
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

    print(q_cam.get_average_freq(), q_cam.queue.num_lost_item.value)
    print(q_back.get_average_freq(), q_back.queue.num_lost_item.value)
    print(q_tracking.get_average_freq())