# This is apparently very important to set. Otherwise OpenCV warpAffine
# takes way to much time when run in a separate process
import os
os.environ["OMP_NUM_THREADS"] = "1"

from camera_tools import Camera, MovieFileCam, BufferedMovieFileCam
from tracker import (
    GridAssignment, MultiFishTracker, MultiFishTracker_CPU, MultiFishOverlay, MultiFishOverlay_opencv, MultiFishTracking,
    AnimalTracker_CPU, AnimalOverlay_opencv, AnimalTrackerParamTracking, AnimalTrackerParamOverlay,  AnimalTracking,
    BodyTracker_CPU, BodyOverlay_opencv, BodyTrackerParamTracking, BodyTrackerParamOverlay,  BodyTracking,
    EyesTracker_CPU, EyesOverlay_opencv, EyesTrackerParamTracking, EyesTrackerParamOverlay,  EyesTracking,
    TailTracker_CPU, TailOverlay_opencv, TailTrackerParamTracking, TailTrackerParamOverlay,  TailTracking
)
from multiprocessing_logger import Logger
from ipc_tools import RingBuffer, QueueMP, MonitoredQueue, ObjectRingBuffer
from video_tools import BackgroundSubtractor, BackgroundImage, Polarity
from image_tools import im2single, im2gray
from dagline import WorkerNode, receive_strategy, send_strategy, ProcessingDAG, plot_logs
from ..stimulus import VisualStimWorker
from ..stimulus.phototaxis import Phototaxis

import numpy as np
from numpy.typing import NDArray, DTypeLike
import time
from typing import Any, Dict, Tuple
import cv2
from functools import partial

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
    
    def work(self, data: None): 
        
        res = self.cam.get_frame()
        elapsed = (time.monotonic_ns() - self.prev_time) 
        while elapsed < 1e9/self.fps:
            elapsed = (time.monotonic_ns() - self.prev_time) 
        self.prev_time = time.monotonic_ns()

        return (res.index, time.perf_counter_ns(), res.image)
    
class BackgroundSubWorker(WorkerNode):

    def __init__(self, sub: BackgroundSubtractor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sub = sub

    def initialize(self) -> None:
        super().initialize()
        self.sub.initialize()

    def work(self, data):
        if data is not None:
            index, timestamp, image = data
            res = self.sub.subtract_background(image)
            return (index, timestamp, res)
         
class TrackerWorker(WorkerNode):
    
    def __init__(self, tracker: MultiFishTracker, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tracker = tracker

    def work(self, data: NDArray) -> Dict:
        if data is not None:
            index, timestamp, image = data
            tracking = self.tracker.track(image)
            if tracking is not None:
                if tracking.body is not None:
                    res = {}
                    indices = list(tracking.body.keys())
                    if indices:
                        k = indices[0]
                        res['stimulus'] = (index, timestamp, tracking.body[k])
                        res['overlay'] = (index, timestamp, tracking)
                
                    return res
        
class OverlayWorker(WorkerNode):

    def __init__(self, overlay: MultiFishOverlay, fps: int = 30, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.overlay = overlay
        self.fps = fps
        self.prev_time = 0

    def work(self, data: Any) -> Dict:
        if data is not None:
            index, timestamp, tracking = data
            if time.monotonic() - self.prev_time > 1/self.fps:
                if tracking.animals.identities is not None:
                    overlay = self.overlay.overlay(tracking.image, tracking)
                    self.prev_time = time.monotonic()
                    return (index, timestamp, overlay)

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
            index, timestamp, image = data
            if time.monotonic() - self.prev_time > 1/self.fps:
                cv2.imshow('display', image) # NOT data[0]
                cv2.waitKey(1)
                self.prev_time = time.monotonic()

if __name__ == "__main__":

    LOGFILE = 'test_tracking_RB.log'
    N_WORKERS = 10
    CAM_FPS = 120
    DATA = [
        ('../toy_data/multi_freelyswimming_1800x1800px.avi', '../toy_data/multi_freelyswimming_1800x1800px.png', Polarity.BRIGHT_ON_DARK, 50),
        ('../toy_data/single_freelyswimming_504x500px.avi', '../toy_data/single_freelyswimming_504x500px.png', Polarity.DARK_ON_BRIGHT, 40),
        ('../toy_data/single_headembedded_544x380px_noparam.avi', '../toy_data/single_headembedded_544x380px_noparam.png', Polarity.DARK_ON_BRIGHT, 100),
        ('../toy_data/single_headembedded_544x380px_param.avi', '../toy_data/single_headembedded_544x380px_param.png', Polarity.DARK_ON_BRIGHT, 100)
    ]
    # background subtracted video
    INPUT_VIDEO, BACKGROUND_IMAGE, BACKGROUND_POLARITY, PIX_PER_MM = DATA[0]

    m = BufferedMovieFileCam(filename=INPUT_VIDEO, memsize_bytes=8e9)
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
        export_fullres_image=True,
        animal=AnimalTracker_CPU(
            assignment=GridAssignment(LUT=np.zeros((h,w), dtype=np.int_)), 
            tracking_param=AnimalTrackerParamTracking(
                pix_per_mm=PIX_PER_MM,
                target_pix_per_mm=5,
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
                pad_value_mm=2.75,
                blur_sz_mm=1/5,
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
    b = BackgroundImage(
        image_file_name = BACKGROUND_IMAGE,
        polarity = BACKGROUND_POLARITY,
        use_gpu=True
    )
    
    ptx = Phototaxis(
        window_size=(1024,1024),
        window_position=(0,0),
        color=(1.0, 0.0, 0.0, 1.0),
        window_decoration=False
    )
    
    cam = CameraWorker(cam = m, fps = CAM_FPS, name='camera', logger = l, receive_strategy=receive_strategy.COLLECT, receive_timeout=1.0)

    bckg = []
    trck = []
    for i in range(N_WORKERS):
        bckg.append(BackgroundSubWorker(b, name=f'background{i}', logger = l, receive_timeout=1.0, profile=True))
        trck.append(TrackerWorker(t, name=f'tracker{i}', logger = l, send_strategy=send_strategy.BROADCAST, receive_timeout=1.0, profile=True))


    dis = Display(fps = 30, name='display', logger = l, receive_timeout=1.0)
    stim = VisualStimWorker(stim=ptx, name='phototaxis', logger=l, receive_timeout=1.0) 
    oly = OverlayWorker(overlay=o, fps=30, name="overlay", logger=l, receive_timeout=1.0)

    # ring buffer camera ------------------------------------------------------------------ 
    dt_uint8_RGB = np.dtype([
        ('index', int, (1,)),
        ('timestamp', float, (1,)), 
        ('image', np.uint8, (h,w,3))
    ])

    def serialize_image(obj: Tuple[int, float, NDArray], data_type: DTypeLike) -> NDArray:
        #tic = time.monotonic_ns() 
        index, timestamp, image = obj
        arr = np.array((index, timestamp, image), dtype = data_type)
        #print(1e-6*(time.monotonic_ns() - tic))
        return arr

    def deserialize_image(arr: NDArray) -> Tuple[int, float, NDArray]:
        index = arr['index'].item()
        timestamp = arr['timestamp'].item()
        image = arr[0]['image']
        return (index, timestamp, image)

    q_cam = MonitoredQueue(
        ObjectRingBuffer(
            num_items = 100,
            data_type = dt_uint8_RGB,
            serialize = partial(serialize_image, data_type=dt_uint8_RGB),
            deserialize = deserialize_image
        )
    )

    q_display = MonitoredQueue(
        ObjectRingBuffer(
            num_items = 100,
            data_type = dt_uint8_RGB,
            serialize = partial(serialize_image, data_type=dt_uint8_RGB),
            deserialize = deserialize_image
        )
    )


    # ring buffer background ------------------------------------------------------------------
    # IMPORTANT: need to copy the data out of the 
    # circular buffer otherwise it can be modified after the fact
    # set copy=True
    
    dt_single_gray = np.dtype([
        ('index', int, (1,)),
        ('timestamp', float, (1,)), 
        ('image', np.float32, (h,w))
    ])

    q_back = []
    for i in range(N_WORKERS):
        q_back.append(MonitoredQueue(
            ObjectRingBuffer(
                num_items = 100,
                data_type = dt_single_gray,
                serialize = partial(serialize_image, data_type=dt_single_gray),
                deserialize = deserialize_image,
                copy=True
            )
        )
        )

    # tracking ring buffer -------------------------------------------------------------------
    # get dtype and itemsize for tracker results
    tracking = t.track(np.zeros((h,w), dtype=np.float32))
    arr_multifish = tracking.to_numpy()

    dt_tracking_multifish = np.dtype([
        ('index', int, (1,)),
        ('timestamp', float, (1,)), 
        ('tracking', arr_multifish.dtype, (1,))
    ])

    def serialize_tracking_multifish(obj: Tuple[int, float, MultiFishTracking], data_type: DTypeLike) -> NDArray:
        index, timestamp, tracking = obj
        return np.array((index, timestamp, tracking.to_numpy()), dtype = data_type)

    def deserialize_tracking_multifish(arr: NDArray) -> Tuple[int, float, MultiFishTracking]:
        index = arr['index'].item()
        timestamp = arr['timestamp'].item()
        tracking = MultiFishTracking.from_numpy(arr[0]['tracking'][0])
        return (index, timestamp, tracking)

    # ---
    dt_tracking_body = np.dtype([
        ('index', int, (1,)),
        ('timestamp', float, (1,)), 
        ('tracking', arr_multifish['bodies'].dtype, (1,))
    ])

    def serialize_tracking_body(obj: Tuple[int, float, BodyTracking], data_type: DTypeLike) -> NDArray:
        index, timestamp, tracking = obj
        return np.array((index, timestamp, tracking.to_numpy()), dtype = data_type)

    def deserialize_tracking_body(arr: NDArray) -> Tuple[int, float, BodyTracking]:
        index = arr['index'].item()
        timestamp = arr['timestamp'].item()
        tracking = BodyTracking.from_numpy(arr[0]['tracking'][0])
        return (index, timestamp, tracking)

    q_tracking = MonitoredQueue(
        ObjectRingBuffer(
            num_items = 100,
            data_type = dt_tracking_body,
            serialize = partial(serialize_tracking_body, data_type=dt_tracking_body),
            deserialize = deserialize_tracking_body
        )
    )

    q_overlay = MonitoredQueue(
        ObjectRingBuffer(
            num_items = 100,
            data_type = dt_tracking_multifish,
            serialize = partial(serialize_tracking_multifish, data_type=dt_tracking_multifish),
            deserialize = deserialize_tracking_multifish
        )
    )

    dag = ProcessingDAG()

    for i in range(N_WORKERS):   
        dag.connect(sender=cam, receiver=bckg[i], queue=q_cam, name='cam_image')
        dag.connect(sender=bckg[i], receiver=trck[i], queue=q_back[i], name='background_subtracted')
        dag.connect(sender=trck[i], receiver=stim, queue=q_tracking, name='stimulus')
        dag.connect(sender=trck[i], receiver=oly, queue=q_overlay, name='overlay')

    dag.connect(sender=oly, receiver=dis, queue=q_display, name='disp')

    l.start()
    dag.start()
    time.sleep(30)
    dag.stop()
    l.stop()

    print('cam to background', q_cam.get_average_freq(),  f'lost: {q_cam.queue.num_lost_item.value}', f'queue size: {q_cam.qsize()}')
    for i in range(N_WORKERS):   
        print(f'background to trackers {i}', q_back[i].get_average_freq(), f'lost: {q_back[i].queue.num_lost_item.value}', f'queue size: {q_back[i].qsize()}')
    print('trackers to visual stim', q_tracking.get_average_freq(), f'lost: {q_tracking.queue.num_lost_item.value}', f'queue size: {q_tracking.qsize()}')
    print('trackers to overlay', q_overlay.get_average_freq(), f'lost: {q_overlay.queue.num_lost_item.value}', f'queue size: {q_overlay.qsize()}')
    print('overlay to display', q_display.get_average_freq(), f'lost: {q_display.queue.num_lost_item.value}', f'queue size: {q_display.qsize()}')

    plot_logs(LOGFILE, outlier_thresh=1000)
    # NOTE: if you have more worker than necessary, you will see a heavy tail in the receive time.
    # This is perfectly normal, each tracker may be skip a few cycles if the others are already 
    # filling the job