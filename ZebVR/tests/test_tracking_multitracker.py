# This is apparently very important to set. Otherwise OpenCV warpAffine
# takes way to much time when run in a separate process
import os
os.environ["OMP_NUM_THREADS"] = "1"

from camera_tools import Camera, MovieFileCam,  BufferedMovieFileCam
from tracker import (
    GridAssignment, MultiFishTracker, MultiFishTracker_CPU, MultiFishOverlay, MultiFishOverlay_opencv,
    AnimalTracker_CPU, AnimalOverlay_opencv, AnimalTrackerParamTracking, AnimalTrackerParamOverlay,
    BodyTracker_CPU, BodyOverlay_opencv, BodyTrackerParamTracking, BodyTrackerParamOverlay,
    EyesTracker_CPU, EyesOverlay_opencv, EyesTrackerParamTracking, EyesTrackerParamOverlay,
    TailTracker_CPU, TailOverlay_opencv, TailTrackerParamTracking, TailTrackerParamOverlay
)
from multiprocessing_logger import Logger
from ipc_tools import RingBuffer, QueueMP, MonitoredQueue
from video_tools import BackgroundSubtractor, BackroundImage, Polarity
from image_tools import im2single, im2gray
from dagline import WorkerNode, receive_strategy, send_strategy, ProcessingDAG, plot_logs
from ZebVR.stimulus import Phototaxis, VisualStimWorker

import numpy as np
from numpy.typing import NDArray
import time
from typing import Any, Dict
import cv2

class CameraWorker(WorkerNode):

    def __init__(self, cam: Camera, fps: int = 200, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cam = cam
        self.prev_time = 0
        self.fps = fps

    def initialize(self) -> None:
        super().initialize()
        self.cam.start_acquisition()

    def cleanup(self) -> None:
        super().cleanup()
        self.cam.stop_acquisition()
    
    def work(self, data: None) -> NDArray: 
        res = self.cam.get_frame().image
        elapsed = (time.monotonic_ns() - self.prev_time) 
        while elapsed < 1e9/self.fps:
            elapsed = (time.monotonic_ns() - self.prev_time) 
        self.prev_time = time.monotonic_ns()
        return res
    
class BackgroundSubWorker(WorkerNode):

    def __init__(self, sub: BackgroundSubtractor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sub = sub

    def initialize(self) -> None:
        super().initialize()
        self.sub.initialize()

    def work(self, data: NDArray) -> NDArray:
        if data is not None:
            image = im2single(im2gray(data))
            return self.sub.subtract_background(image)
         
class TrackerWorker(WorkerNode):
    
    def __init__(self, tracker: MultiFishTracker, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tracker = tracker

    def work(self, data: NDArray) -> Dict:
        if data is not None:
            tracking = self.tracker.track(data)
            if tracking is not None:
                if tracking.body is not None:
                    res = {}
                    indices = list(tracking.body.keys())
                    if indices:
                        k = indices[0]
                        res['stimulus'] = tracking.body[k]
                        res['overlay'] = tracking
                    return res
        
class OverlayWorker(WorkerNode):

    def __init__(self, overlay: MultiFishOverlay, fps: int = 30, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.overlay = overlay
        self.fps = fps
        self.prev_time = 0

    def work(self, data: Any) -> Dict:
        if data is not None:
            if time.monotonic() - self.prev_time > 1/self.fps:
                if data.animals.identities is not None:
                    overlay = self.overlay.overlay(data.image, data)
                    self.prev_time = time.monotonic()
                    return overlay

class Display(WorkerNode):

    def __init__(self, fps: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fps = fps
        self.prev_time = 0

    def initialize(self) -> None:
        super().initialize()
        cv2.namedWindow('display')
    
    def cleanup(self) -> None:
        super().cleanup()
        cv2.destroyAllWindows()

    def work(self, data: NDArray) -> None:
        if data is not None:
            if time.monotonic() - self.prev_time > 1/self.fps:
                cv2.imshow('display', data)
                cv2.waitKey(1)
                self.prev_time = time.monotonic()

if __name__ == "__main__":

    PIX_PER_MM = 40  
    LOGFILE = 'test_tracking.log'
    N_BACKGROUND_WORKERS = 2
    N_TRACKER_WORKERS = 6
    CAM_FPS = 550

    m = BufferedMovieFileCam(filename='toy_data/freely_swimming_param.avi', memsize_bytes=16e9)
    #m = MovieFileCam(filename='toy_data/freely_swimming_param.avi')
    h, w = (m.get_height(), m.get_width())

    o = MultiFishOverlay_opencv(
        AnimalOverlay_opencv(AnimalTrackerParamOverlay()),
        BodyOverlay_opencv(BodyTrackerParamOverlay()),
        EyesOverlay_opencv(EyesTrackerParamOverlay()),
        TailOverlay_opencv(TailTrackerParamOverlay()),
    )
    
    t = MultiFishTracker_CPU(
        max_num_animals=1,
        accumulator=None, 
        animal=AnimalTracker_CPU(
            assignment=GridAssignment(LUT=np.zeros((h,w), dtype=np.int_)), 
            tracking_param=AnimalTrackerParamTracking(
                pix_per_mm=PIX_PER_MM,
                target_pix_per_mm=7.5,
                animal_intensity=0.07,
                animal_brightness=0.0,
                animal_gamma=1.0,
                animal_contrast=1.0,
                min_animal_size_mm=1.0,
                max_animal_size_mm=30.0,
                min_animal_length_mm=0,
                max_animal_length_mm=0,
                min_animal_width_mm=0,
                max_animal_width_mm=0,
                pad_value_mm=4.0,
                blur_sz_mm=1/7.5,
                median_filter_sz_mm=0,
            )
        ),
        body=BodyTracker_CPU(
            tracking_param=BodyTrackerParamTracking(
                pix_per_mm=PIX_PER_MM,
                target_pix_per_mm=10,
                body_intensity=0.20,
                body_brightness=0.0,
                body_gamma=1.0,
                body_contrast=3.0,
                min_body_size_mm=0.0,
                max_body_size_mm=30.0,
                min_body_length_mm=0,
                max_body_length_mm=0,
                min_body_width_mm=0,
                max_body_width_mm=0,
                blur_sz_mm=1/7.5,
                median_filter_sz_mm=0,
            )
        ),
        eyes=EyesTracker_CPU(
            tracking_param=EyesTrackerParamTracking(
                pix_per_mm=PIX_PER_MM,
                target_pix_per_mm=40,
                eye_brightness=0.0,
                eye_gamma=3.0,
                eye_dyntresh_res=10,
                eye_contrast=5.0,
                eye_size_lo_mm=0.8,
                eye_size_hi_mm=10.0,
                blur_sz_mm=0.06,
                median_filter_sz_mm=0,
                crop_dimension_mm=(1.0,1.5),
                crop_offset_mm=-0.75
            )
        ),
        tail=TailTracker_CPU(
            tracking_param=TailTrackerParamTracking(
                pix_per_mm=PIX_PER_MM,
                target_pix_per_mm=20,
                ball_radius_mm=0.05,
                arc_angle_deg=90,
                n_tail_points=6,
                n_pts_arc=20,
                n_pts_interp=40,
                tail_length_mm=2.2,
                dist_swim_bladder_mm=0.0,
                blur_sz_mm=0.06,
                median_filter_sz_mm=0,
                tail_brightness=0.0,
                tail_contrast=3.0,
                tail_gamma=0.75,
                crop_dimension_mm=(3.5,3.5),
                crop_offset_tail_mm=1.75
            )
        )
    )

    l = Logger(LOGFILE, Logger.INFO)
    b = BackroundImage(
        image_file_name = 'toy_data/freely_swimming_param.png',
        polarity = Polarity.DARK_ON_BRIGHT
    )
    
    ptx = Phototaxis(
        window_size=(1024,1024),
        window_position=(0,0),
        color=(1.0, 0.0, 0.0, 1.0),
        window_decoration=False
    )
    
    cam = CameraWorker(cam = m, fps = CAM_FPS, name='camera', logger = l, receive_strategy=receive_strategy.COLLECT, receive_timeout=1.0)
    bckg = []
    for i in range(N_BACKGROUND_WORKERS):
        bckg.append(BackgroundSubWorker(b, name=f'background{i}', logger = l, receive_timeout=1.0, profile=False))

    trck = []
    for i in range(N_TRACKER_WORKERS):
        trck.append(TrackerWorker(t, name=f'tracker{i}', logger = l, send_strategy=send_strategy.BROADCAST, receive_timeout=1.0))

    dis = Display(fps = 30, name='display', logger = l, receive_timeout=1.0)
    stim = VisualStimWorker(stim=ptx, name='phototaxis', logger=l, receive_timeout=1.0) 
    oly = OverlayWorker(overlay=o, fps=30, name="overlay", logger=l, receive_timeout=1.0)

    q_cam = MonitoredQueue(
        RingBuffer(
            num_items = 100,
            item_shape = (h, w, 3),
            data_type = np.uint8
        )
    )

    # IMPORTANT: need to copy the data out of the 
    # circular buffer otherwise it can be modified after the fact
    q_back = MonitoredQueue(
        RingBuffer(
            num_items = 100,
            item_shape = (h, w),
            data_type = np.float32,
            copy=True
        )
    )
    q_display = MonitoredQueue(
        RingBuffer(
            num_items = 100,
            item_shape = (h, w, 3),
            data_type = np.uint8
        )
    )
    #q_display = MonitoredQueue(QueueMP())
    q_tracking = MonitoredQueue(QueueMP())
    q_overlay = MonitoredQueue(QueueMP())

    '''
    q_cam = MonitoredQueue(QueueMP())
    q_back = MonitoredQueue(QueueMP())
    q_display = MonitoredQueue(QueueMP())
    q_tracking = MonitoredQueue(QueueMP())
    '''

    '''
    q_cam = MonitoredQueue(ZMQ_PushPullObj(port=5556))
    q_back = MonitoredQueue(ZMQ_PushPullObj(port=5557))
    q_display = MonitoredQueue(ZMQ_PushPullObj(port=5558))
    q_tracking = MonitoredQueue(ZMQ_PushPullObj(port=5559)) 
    '''

    dag = ProcessingDAG()

    for i in range(N_BACKGROUND_WORKERS):   
        dag.connect(sender=cam, receiver=bckg[i], queue=q_cam, name='cam_image')
    
    for i in range(N_BACKGROUND_WORKERS):
        for j in range(N_TRACKER_WORKERS):
            dag.connect(sender=bckg[i], receiver=trck[j], queue=q_back, name='background_subtracted')

    for i in range(N_TRACKER_WORKERS):
        dag.connect(sender=trck[i], receiver=stim, queue=q_tracking, name='stimulus')
        dag.connect(sender=trck[i], receiver=oly, queue=q_overlay, name='overlay')

    dag.connect(sender=oly, receiver=dis, queue=q_display, name='disp')


    l.start()
    dag.start()
    time.sleep(30)
    dag.stop()
    l.stop()
    

    print('cam to background', q_cam.get_average_freq(), q_cam.queue.num_lost_item.value)
    print('background to trackers', q_back.get_average_freq(), q_back.queue.num_lost_item.value)
    print('trackers to visual stim', q_tracking.get_average_freq())
    print('trackers to overlay', q_overlay.get_average_freq())
    print('overlay to display', q_display.get_average_freq(), q_display.queue.num_lost_item.value)

    plot_logs(LOGFILE, outlier_thresh=1000)