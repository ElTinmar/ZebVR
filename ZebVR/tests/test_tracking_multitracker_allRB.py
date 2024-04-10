# This is apparently very important to set. Otherwise OpenCV warpAffine
# takes way to much time when run in a separate process
import os
os.environ["OMP_NUM_THREADS"] = "1"

from camera_tools import Camera, MovieFileCam
from tracker import (
    GridAssignment, MultiFishTracker, MultiFishTracker_CPU, MultiFishOverlay, MultiFishOverlay_opencv, MultiFishTracking,
    AnimalTracker_CPU, AnimalOverlay_opencv, AnimalTrackerParamTracking, AnimalTrackerParamOverlay,  AnimalTracking,
    BodyTracker_CPU, BodyOverlay_opencv, BodyTrackerParamTracking, BodyTrackerParamOverlay,  BodyTracking,
    EyesTracker_CPU, EyesOverlay_opencv, EyesTrackerParamTracking, EyesTrackerParamOverlay,  EyesTracking,
    TailTracker_CPU, TailOverlay_opencv, TailTrackerParamTracking, TailTrackerParamOverlay,  TailTracking
)
from multiprocessing_logger import Logger
from ipc_tools import RingBuffer, QueueMP, MonitoredQueue
from video_tools import BackgroundSubtractor, BackroundImage, Polarity
from image_tools import im2single, im2gray
from dagline import WorkerNode, receive_strategy, send_strategy, ProcessingDAG, plot_logs
from ZebVR.stimulus import VisualStimWorker
from ZebVR.stimulus.phototaxis_RB import Phototaxis

import numpy as np
from numpy.typing import NDArray
import time
from typing import Any, Dict
import cv2

#TODO do something with that [0] indexing

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
        
        res = self.cam.get_frame()
        elapsed = (time.monotonic_ns() - self.prev_time) 
        while elapsed < 1e9/self.fps:
            elapsed = (time.monotonic_ns() - self.prev_time) 
        self.prev_time = time.monotonic_ns()
                
        arr = np.array(
            (res.timestamp, res.index, res.image),
            dtype = np.dtype([
                ('timestamp', np.float64, (1,)), 
                ('index', int, (1,)),
                ('image', np.uint8, (h,w,3))
            ])
        )
        return arr
    
class BackgroundSubWorker(WorkerNode):

    def __init__(self, sub: BackgroundSubtractor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sub = sub

    def initialize(self) -> None:
        super().initialize()
        self.sub.initialize()

    def work(self, data: NDArray) -> NDArray:
        if data is not None:
            
            #0
            #t0_ns = time.monotonic_ns()
            timestamp, index, image = data[0]
            #print('indexing', 1e-6*(time.monotonic_ns()-t0_ns))

            #1
            res = self.sub.subtract_background(im2single(im2gray(image)))

            #2 NOTE structured arrays are SLOW. This step takes a lot of extra time, use MultiRingBuffer instead
            #t0_ns = time.monotonic_ns()
            arr = np.array(
                (timestamp[0], index[0], res),
                dtype = np.dtype([
                    ('timestamp', np.float64, (1,)), 
                    ('index', int, (1,)),
                    ('image', np.float32, (h,w))
                ], align=True)
            )
            #print('creation', 1e-6*(time.monotonic_ns()-t0_ns))

            return arr
         
class TrackerWorker(WorkerNode):
    
    def __init__(self, tracker: MultiFishTracker, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tracker = tracker

    def work(self, data: NDArray) -> Dict:
        if data is not None:
            tracking = self.tracker.track(data[0]['image'])
            if tracking is not None:
                if tracking.body is not None:
                    res = {}
                    indices = list(tracking.body.keys())
                    if indices:
                        k = indices[0]
                        tracking_arr = tracking.to_numpy()
                        res['stimulus'] = tracking_arr['bodies'][k] 
                        res['overlay'] = tracking_arr
                    return res
        
class OverlayWorker(WorkerNode):

    def __init__(self, overlay: MultiFishOverlay, fps: int = 30, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.overlay = overlay
        self.fps = fps
        self.prev_time = 0

    def work(self, data: Any) -> Dict:
        if data is not None:
            tracking = MultiFishTracking.from_numpy(data[0])
            if time.monotonic() - self.prev_time > 1/self.fps:
                if tracking.animals.identities is None:
                    return tracking.image
                else:
                    overlay = self.overlay.overlay(tracking.image, tracking)
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
                cv2.imshow('display', data) # NOT data[0]
                cv2.waitKey(1)
                self.prev_time = time.monotonic()

if __name__ == "__main__":

    PIX_PER_MM = 40  
    LOGFILE = 'test_tracking_RB.log'

    m = MovieFileCam(filename='toy_data/freely_swimming_param.avi')
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
    
    cam = CameraWorker(cam = m, fps = 300, name='camera', logger = l, receive_strategy=receive_strategy.COLLECT, receive_timeout=1.0)

    bckg0 = BackgroundSubWorker(b, name='background0', logger = l, receive_timeout=1.0)
    bckg1 = BackgroundSubWorker(b, name='background1', logger = l, receive_timeout=1.0)

    trck0 = TrackerWorker(t, name='tracker0', logger = l, send_strategy=send_strategy.BROADCAST, receive_timeout=1.0)
    trck1 = TrackerWorker(t, name='tracker1', logger = l, send_strategy=send_strategy.BROADCAST, receive_timeout=1.0)
    trck2 = TrackerWorker(t, name='tracker2', logger = l, send_strategy=send_strategy.BROADCAST, receive_timeout=1.0)
    trck3 = TrackerWorker(t, name='tracker3', logger = l, send_strategy=send_strategy.BROADCAST, receive_timeout=1.0)

    dis = Display(fps = 30, name='display', logger = l, receive_timeout=1.0)
    stim = VisualStimWorker(stim=ptx, name='phototaxis', logger=l, receive_timeout=1.0) 
    oly = OverlayWorker(overlay=o, fps=30, name="overlay", logger=l, receive_timeout=1.0)

    q_cam = MonitoredQueue(
        RingBuffer(
            num_items = 100,
            item_shape = (1,),
            data_type = np.dtype([
                ('timestamp', np.float64, (1,)), 
                ('index', int, (1,)),
                ('image', np.uint8, (h,w,3))
            ])
        )
    )

    # IMPORTANT: need to copy the data out of the 
    # circular buffer otherwise it can be modified after the fact
    q_back = MonitoredQueue(
        RingBuffer(
            num_items = 100,
            item_shape = (1,),
            data_type = np.dtype([
                ('timestamp', np.float64, (1,)), 
                ('index', int, (1,)),
                ('image', np.float32, (h,w))
            ]),
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

    # get dtype and itemsize for tracker results
    tracking = t.track(np.zeros((h,w), dtype=np.float32))
    arr_multifish = tracking.to_numpy()

    q_tracking = MonitoredQueue(
        RingBuffer(
            num_items = 100,
            item_shape = (1,),
            data_type = arr_multifish['bodies'].dtype
        )
    )

    q_overlay = MonitoredQueue(
        RingBuffer(
            num_items = 100,
            item_shape = (1,),
            data_type = arr_multifish.dtype
        )
    )

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
    dag.connect(sender=cam, receiver=bckg0, queue=q_cam, name='cam_image')
    dag.connect(sender=cam, receiver=bckg1, queue=q_cam, name='cam_image')
    
    dag.connect(sender=bckg0, receiver=trck0, queue=q_back, name='background_subtracted')
    dag.connect(sender=bckg0, receiver=trck1, queue=q_back, name='background_subtracted')
    dag.connect(sender=bckg0, receiver=trck2, queue=q_back, name='background_subtracted')
    dag.connect(sender=bckg0, receiver=trck3, queue=q_back, name='background_subtracted')

    dag.connect(sender=bckg1, receiver=trck0, queue=q_back, name='background_subtracted')
    dag.connect(sender=bckg1, receiver=trck1, queue=q_back, name='background_subtracted')
    dag.connect(sender=bckg1, receiver=trck2, queue=q_back, name='background_subtracted')
    dag.connect(sender=bckg1, receiver=trck3, queue=q_back, name='background_subtracted')

    dag.connect(sender=trck0, receiver=stim, queue=q_tracking, name='stimulus')
    dag.connect(sender=trck1, receiver=stim, queue=q_tracking, name='stimulus')
    dag.connect(sender=trck2, receiver=stim, queue=q_tracking, name='stimulus')
    dag.connect(sender=trck3, receiver=stim, queue=q_tracking, name='stimulus')

    dag.connect(sender=trck0, receiver=oly, queue=q_overlay, name='overlay')
    dag.connect(sender=trck1, receiver=oly, queue=q_overlay, name='overlay')
    dag.connect(sender=trck2, receiver=oly, queue=q_overlay, name='overlay')
    dag.connect(sender=trck3, receiver=oly, queue=q_overlay, name='overlay')

    dag.connect(sender=oly, receiver=dis, queue=q_display, name='disp')

    l.start()
    dag.start()
    time.sleep(30)
    dag.stop()
    l.stop()

    print('cam to background', q_cam.get_average_freq(), q_cam.queue.num_lost_item.value)
    print('background to trackers', q_back.get_average_freq(), q_back.queue.num_lost_item.value)
    print('trackers to visual stim', q_tracking.get_average_freq(), q_tracking.queue.num_lost_item.value)
    print('trackers to overlay', q_overlay.get_average_freq(), q_overlay.queue.num_lost_item.value)
    print('overlay to display', q_display.get_average_freq(), q_display.queue.num_lost_item.value)

    plot_logs(LOGFILE, outlier_thresh=1000)