# This is apparently very important to set. Otherwise OpenCV warpAffine
# takes way to much time when run in a separate process
import os
os.environ["OMP_NUM_THREADS"] = "1"

from camera_tools import Camera, XimeaCamera
from tracker import (
    GridAssignment, MultiFishTracker, MultiFishTracker_CPU, MultiFishOverlay, MultiFishOverlay_opencv, MultiFishTracking,
    AnimalTracker_CPU, AnimalOverlay_opencv, AnimalTrackerParamTracking, AnimalTrackerParamOverlay, 
    BodyTracker_CPU, BodyOverlay_opencv, BodyTrackerParamTracking, BodyTrackerParamOverlay,  
)
from multiprocessing_logger import Logger
from ipc_tools import MonitoredQueue, ObjectRingBuffer2, QueueMP
from video_tools import BackgroundSubtractor, BackroundImage
from image_tools import im2single, im2gray
from dagline import WorkerNode, receive_strategy, send_strategy, ProcessingDAG
from ZebVR.stimulus import VisualStimWorker, Phototaxis, OMR, OKR, PreyCapture, Looming, DotMotion

import numpy as np
from numpy.typing import NDArray, DTypeLike
import time
from typing import Callable, Any, Dict, Tuple, Optional
import cv2
import json

from dagline import plot_logs as plot_worker_logs
from ipc_tools import plot_logs as plot_queue_logs

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox
from qt_widgets import LabeledDoubleSpinBox, LabeledSliderDoubleSpinBox, NDarray_to_QPixmap


from ZebVR.config import (
    CALIBRATION_FILE, CAM_WIDTH, CAM_HEIGHT,
    CAM_EXPOSURE_MS, CAM_GAIN, CAM_FPS,
    CAM_OFFSETX, CAM_OFFSETY, 
    PROJ_WIDTH, PROJ_HEIGHT, PROJ_POS, PROJ_FPS,
    PIXEL_SCALING, BACKGROUND_FILE, IMAGE_FOLDER,
    POLARITY, ANIMAL_TRACKING_PARAM,
    BODY_TRACKING_PARAM, FOREGROUND_COLOR, 
    BACKGROUND_COLOR
)

class CameraGui(WorkerNode):

    def initialize(self) -> None:
        super().initialize()
        
        self.updated = False
        self.app = QApplication([])
        self.window = QWidget()
        self.controls = [
            'framerate', 
            'exposure', 
            'gain', 
            'offsetX', 
            'offsetY', 
            'height', 
            'width'
        ]
        self.declare_components()
        self.layout_components()
        self.window.show()

    def declare_components(self):

        # Basic camera controls ----------------------------------
         
        self.start_button = QPushButton()
        self.start_button.setText('acquire')
        self.start_button.setCheckable(True)
        self.start_button.toggled.connect(self.on_change)

        # controls 
        for c in self.controls:
            self.create_spinbox(c)

        # Region of interest ------------------------------------

        self.ROI_groupbox = QGroupBox('ROI:')

    def create_spinbox(self, attr: str):
        '''
        Creates spinbox with correct label, value, range and increment
        as specified by the camera object. Connects to relevant
        callback.
        WARNING This is compact but a bit terse and introduces dependencies
        in the code. 
        '''
        if attr in ['framerate', 'exposure', 'gain']:
            setattr(self, attr + '_spinbox', LabeledSliderDoubleSpinBox())
        else:
            setattr(self, attr + '_spinbox', LabeledDoubleSpinBox())
        spinbox = getattr(self, attr + '_spinbox')
        spinbox.setText(attr)
        spinbox.setRange(0,100_000)
        spinbox.setSingleStep(1)
        spinbox.setValue(0)
        spinbox.valueChanged.connect(self.on_change)

    def layout_components(self):

        layout_frame = QVBoxLayout(self.ROI_groupbox)
        layout_frame.addStretch()
        layout_frame.addWidget(self.offsetX_spinbox)
        layout_frame.addWidget(self.offsetY_spinbox)
        layout_frame.addWidget(self.height_spinbox)
        layout_frame.addWidget(self.width_spinbox)
        layout_frame.addStretch()

        layout_controls = QVBoxLayout(self.window)
        layout_controls.addStretch()
        layout_controls.addWidget(self.exposure_spinbox)
        layout_controls.addWidget(self.gain_spinbox)
        layout_controls.addWidget(self.framerate_spinbox)
        layout_controls.addWidget(self.ROI_groupbox)
        layout_controls.addWidget(self.start_button)
        layout_controls.addStretch()

    def on_change(self):
        self.updated = True

    def process_data(self, data: None) -> NDArray:
        self.app.processEvents()

    def block_signals(self, block):
        for widget in self.window.findChildren(QWidget):
            widget.blockSignals(block)

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        # receive cam inof
        info = metadata['camera_info']
        if info is not None: 
            print(info)
            self.block_signals(True)
            for c in self.controls:
                spinbox = getattr(self, c + '_spinbox')
                spinbox.setValue(info[c]['value'])
                spinbox.setRange(info[c]['min'], info[c]['max'])
                spinbox.setSingleStep(info[c]['increment'])
            self.block_signals(False)

        # send only one message when things are changed
        if self.updated:
            res = {}
            res['camera_control'] = {}
            res['camera_control']['acquire'] = self.start_button.isChecked()
            for c in self.controls:
                spinbox = getattr(self, c + '_spinbox')
                res['camera_control'][c] = spinbox.value()
            self.updated = False
            return res       
        else:
            return None
        
class CameraWorker(WorkerNode):

    def __init__(
            self, 
            camera_constructor: Callable[[Camera], None], 
            exposure: float,
            gain: float,
            framerate: float,
            height: int,
            width: int,
            offsetx: int,
            offsety: int,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.camera_constructor = camera_constructor
        self.exposure = exposure
        self.gain = gain
        self.framerate = framerate
        self.height = height
        self.width = width
        self.offsetx = offsetx
        self.offsety = offsety
        self.updated = False
    
    def initialize(self) -> None:
        super().initialize()
        self.cam = self.camera_constructor()
        self.cam.set_exposure(self.exposure)
        self.cam.set_gain(self.gain)
        self.cam.set_framerate(self.framerate)
        self.cam.set_height(self.height)
        self.cam.set_width(self.width)
        self.cam.set_offsetX(self.offsetx)
        self.cam.set_offsetY(self.offsety)
        self.cam.start_acquisition()
        self.updated = True

    def cleanup(self) -> None:
        super().cleanup()
        self.cam.stop_acquisition()
    
    def process_data(self, data: None): 
        frame = self.cam.get_frame()
        if frame:
            res = {}
            res['background_subtraction'] = (frame.index, time.perf_counter_ns(), frame.image)
            res['image_saver'] = (frame.index, time.perf_counter_ns(), frame.image)
            return res
        
    def process_metadata(self, metadata) -> Any:
        # receive
        control = metadata['camera_control']
        if control is not None: 
            self.cam.stop_acquisition()
            self.cam.set_exposure(control['exposure'])
            self.cam.set_gain(control['gain'])
            self.cam.set_framerate(control['framerate'])
            self.cam.set_height(control['height'])
            self.cam.set_width(control['width'])
            self.cam.set_offsetX(control['offsetX'])
            self.cam.set_offsetY(control['offsetY'])
            self.cam.start_acquisition()
            self.updated = True
        
        # send
        # if camera settings were updated, send info
        if self.updated:
            self.updated = False
            res = {}
            res['camera_info'] = {}
            res['camera_info']['exposure'] = {}
            res['camera_info']['gain'] = {}
            res['camera_info']['framerate'] = {}
            res['camera_info']['height'] = {}
            res['camera_info']['width'] = {}
            res['camera_info']['offsetX'] = {}
            res['camera_info']['offsetY'] = {}
            res['camera_info']['exposure']['value'] = self.cam.get_exposure()
            res['camera_info']['exposure']['min'], res['camera_info']['exposure']['max'] = self.cam.get_exposure_range()
            res['camera_info']['exposure']['increment'] = self.cam.get_exposure_increment()
            res['camera_info']['gain']['value'] = self.cam.get_gain()
            res['camera_info']['gain']['min'], res['camera_info']['exposure']['max'] = self.cam.get_gain_range()
            res['camera_info']['gain']['increment'] = self.cam.get_gain_increment()
            res['camera_info']['framerate']['value'] = self.cam.get_framerate()
            res['camera_info']['framerate']['min'], res['camera_info']['exposure']['max'] = self.cam.get_framerate_range()
            res['camera_info']['framerate']['increment'] = self.cam.get_framerate_increment()
            res['camera_info']['height']['value'] = self.cam.get_height()
            res['camera_info']['height']['min'], res['camera_info']['exposure']['max'] = self.cam.get_height_range()
            res['camera_info']['height']['increment'] = self.cam.get_height_increment()
            res['camera_info']['width']['value'] = self.cam.get_width()
            res['camera_info']['width']['min'], res['camera_info']['exposure']['max'] = self.cam.get_width_range()
            res['camera_info']['width']['increment'] = self.cam.get_width_increment()
            res['camera_info']['offsetX']['value'] = self.cam.get_offsetX()
            res['camera_info']['offsetX']['min'], res['camera_info']['exposure']['max'] = self.cam.get_offsetX_range()
            res['camera_info']['offsetX']['increment'] = self.cam.get_offsetX_increment()
            res['camera_info']['offsetY']['value'] = self.cam.get_offsetY()
            res['camera_info']['offsetY']['min'], res['camera_info']['exposure']['max'] = self.cam.get_offsetY_range()
            res['camera_info']['offsetY']['increment'] = self.cam.get_offsetY_increment()
            return res

class BackgroundSubWorker(WorkerNode):

    def __init__(self, sub: BackgroundSubtractor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sub = sub

    def initialize(self) -> None:
        super().initialize()
        self.sub.initialize()

    def process_data(self, data):
        if data is not None:
            index, timestamp, image = data
            res = self.sub.subtract_background(image)
            return (index, timestamp, res)

    def process_metadata(self, metadata) -> Any:
        pass

class TrackerWorker(WorkerNode):
    
    def __init__(self, tracker: MultiFishTracker, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tracker = tracker

    def initialize(self) -> None:
        super().initialize()

        # try to trigger numba compilation during init phase (doesn't work right now)
        # self.tracker.tail.track(np.zeros((100,100),dtype=np.float32), centroid=np.array([0,0]))

    def process_data(self, data: NDArray) -> Dict:
        try:
            index, timestamp, image = data
            tracking = self.tracker.track(image)
            res = {}
            k = tracking.animals.identities[0]
            res['stimulus'] = (index, timestamp, tracking.animals.centroids[k,:], tracking.body[k].heading[:,1])
            res['overlay'] = (index, timestamp, tracking)
            return res
        except:
            return None  
        
    def process_metadata(self, metadata) -> Any:
        pass

class OverlayWorker(WorkerNode):

    def __init__(self, overlay: MultiFishOverlay, fps: int = 30, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.overlay = overlay
        self.fps = fps
        self.prev_time = 0

    def process_data(self, data: Any) -> Dict:
        if data is not None:
            index, timestamp, tracking = data
            if time.monotonic() - self.prev_time > 1/self.fps:
                if tracking.animals.identities is not None:
                    overlay = self.overlay.overlay(tracking.image, tracking)
                    self.prev_time = time.monotonic()
                    return (index, timestamp, overlay)

    def process_metadata(self, metadata) -> Any:
        pass

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

    def process_data(self, data: NDArray) -> None:
        if data is not None:
            index, timestamp, image = data
            if time.monotonic() - self.prev_time > 1/self.fps:
                cv2.imshow('display', image) # NOT data[0]
                cv2.waitKey(1)
                self.prev_time = time.monotonic()

    def process_metadata(self, metadata) -> Any:
        pass

class ImageSaver(WorkerNode):

    def __init__(self, folder: str, zero_padding: int = 8, compress: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.folder = folder
        self.zero_padding = zero_padding
        self.compress = compress

    def initialize(self) -> None:
        super().initialize()
        if not os.path.exists(self.folder):
            os.mkdir(self.folder)

    def process_data(self, data: NDArray) -> None:
        if data is not None:
            index, timestamp, image = data
            image_resized = cv2.resize(image,None,None,0.25,0.25,cv2.INTER_NEAREST)
            metadata = np.array( 
                (index, timestamp), 
                dtype = np.dtype([('index',np.int64), ('timestamp',np.float32)]) 
            )
            filename = os.path.join(self.folder, f'{index:0{self.zero_padding}}')
            if self.compress:
                np.savez_compressed(filename, image=image_resized, metadata=metadata)
            else:
                np.savez(filename, image=image_resized, metadata=metadata)

    def process_metadata(self, metadata) -> Any:
        pass
    
if __name__ == "__main__":

    LOGFILE_WORKERS = 'workers.log'
    LOGFILE_QUEUES = 'queues.log'

    # TODO profile with just one worker, otherwise lot of time waiting for data
    N_BACKGROUND_WORKERS = 1
    N_TRACKER_WORKERS = 1
    BACKGROUND_GPU = True
    T_REFRESH = 1e-4

    DURATION_S = 60
    RECORD_VIDEO = False
    DARKLEFT = True

    with open(CALIBRATION_FILE, 'r') as f:
        calibration = json.load(f)

    o = MultiFishOverlay_opencv(
        AnimalOverlay_opencv(AnimalTrackerParamOverlay()),
        BodyOverlay_opencv(BodyTrackerParamOverlay()),
        None,
        None,
    )
    
    t = MultiFishTracker_CPU(
        max_num_animals=1,
        accumulator=None, 
        export_fullres_image=True,
        downsample_fullres_export=0.25,
        animal=AnimalTracker_CPU(
            assignment=GridAssignment(LUT=np.zeros((CAM_HEIGHT,CAM_WIDTH), dtype=np.int_)), 
            tracking_param=AnimalTrackerParamTracking(**ANIMAL_TRACKING_PARAM)
        ),
        body=BodyTracker_CPU(tracking_param=BodyTrackerParamTracking(**BODY_TRACKING_PARAM)),
        eyes=None,
        tail=None
    )

    worker_logger = Logger(LOGFILE_WORKERS, Logger.INFO)
    queue_logger = Logger(LOGFILE_QUEUES, Logger.INFO)

    b = BackroundImage(
        image_file_name = BACKGROUND_FILE,
        polarity = POLARITY,
        use_gpu = BACKGROUND_GPU
    )
    
    ptx = Phototaxis(
        window_size=(PROJ_WIDTH, PROJ_HEIGHT),
        window_position=PROJ_POS,
        foreground_color=FOREGROUND_COLOR,
        background_color=BACKGROUND_COLOR,
        window_decoration=False,
        transformation_matrix=np.array(calibration['cam_to_proj'], dtype=np.float32),
        refresh_rate=PROJ_FPS,
        vsync=True,
        pixel_scaling=PIXEL_SCALING,
        darkleft = DARKLEFT
    )

    omr = OMR(
        window_size=(PROJ_WIDTH, PROJ_HEIGHT),
        window_position=PROJ_POS,
        foreground_color=FOREGROUND_COLOR,
        background_color=BACKGROUND_COLOR,        
        window_decoration=False,
        transformation_matrix=np.array(calibration['cam_to_proj'], dtype=np.float32),
        refresh_rate=PROJ_FPS,
        vsync=True,
        pixel_scaling=PIXEL_SCALING
    )

    okr = OKR(
        window_size=(PROJ_WIDTH, PROJ_HEIGHT),
        window_position=PROJ_POS,
        foreground_color=FOREGROUND_COLOR,
        background_color=BACKGROUND_COLOR,        
        window_decoration=False,
        transformation_matrix=np.array(calibration['cam_to_proj'], dtype=np.float32),
        refresh_rate=PROJ_FPS,
        vsync=True,
        pixel_scaling=PIXEL_SCALING
    )

    looming = Looming(
        window_size=(PROJ_WIDTH, PROJ_HEIGHT),
        window_position=PROJ_POS,
        foreground_color=FOREGROUND_COLOR,
        background_color=BACKGROUND_COLOR,        
        window_decoration=False,
        transformation_matrix=np.array(calibration['cam_to_proj'], dtype=np.float32),
        refresh_rate=PROJ_FPS,
        vsync=True,
        pixel_scaling=PIXEL_SCALING
    )

    preycapture = PreyCapture(
        window_size=(PROJ_WIDTH, PROJ_HEIGHT),
        window_position=PROJ_POS,
        foreground_color=FOREGROUND_COLOR,
        background_color=BACKGROUND_COLOR,        
        window_decoration=False,
        transformation_matrix=np.array(calibration['cam_to_proj'], dtype=np.float32),
        refresh_rate=PROJ_FPS,
        vsync=True,
        pixel_scaling=PIXEL_SCALING
    )

    cam_control = CameraGui(
        name='cam_gui',  
        logger=worker_logger, 
        logger_queues=queue_logger
    )
    
    cam = CameraWorker(
        camera_constructor = XimeaCamera, 
        exposure = CAM_EXPOSURE_MS,
        gain = CAM_GAIN,
        framerate = CAM_FPS,
        height = CAM_HEIGHT,
        width = CAM_WIDTH,
        offsetx = CAM_OFFSETX,
        offsety = CAM_OFFSETY,
        name='camera', 
        logger=worker_logger, 
        logger_queues=queue_logger, 
        receive_data_strategy=receive_strategy.COLLECT, 
        send_data_strategy=send_strategy.BROADCAST, 
        receive_data_timeout=1.0
    )

    image_saver = ImageSaver(
        folder = IMAGE_FOLDER, 
        name='image_saver',  
        logger=worker_logger, 
        logger_queues=queue_logger, 
        receive_data_timeout=1.0
    )

    bckg = []
    for i in range(N_BACKGROUND_WORKERS):
        bckg.append(BackgroundSubWorker(b, name=f'background{i}', logger=worker_logger, logger_queues=queue_logger, receive_data_timeout=1.0, profile=False))

    trck = []
    for i in range(N_TRACKER_WORKERS):
        trck.append(TrackerWorker(t, name=f'tracker{i}', logger=worker_logger, logger_queues=queue_logger, send_data_strategy=send_strategy.BROADCAST, receive_data_timeout=1.0, profile=False))

    dis = Display(
        fps=30, 
        name='display', 
        logger=worker_logger, 
        logger_queues=queue_logger, 
        receive_data_timeout=1.0
    )

    stim = VisualStimWorker(
        stim=ptx, 
        name='phototaxis', 
        logger=worker_logger, 
        logger_queues=queue_logger, 
        receive_data_timeout=1.0
    )

    oly = OverlayWorker(
        overlay=o, 
        fps=30, 
        name="overlay", 
        logger=worker_logger, 
        logger_queues=queue_logger, 
        receive_data_timeout=1.0
    )

    # ring buffer camera ------------------------------------------------------------------ 
    dt_uint8_RGB = np.dtype([
        ('index', int, (1,)),
        ('timestamp', float, (1,)), 
        ('image', np.uint8, (CAM_HEIGHT,CAM_WIDTH,3))
    ])

    dt_uint8_gray = np.dtype([
        ('index', int, (1,)),
        ('timestamp', float, (1,)), 
        ('image', np.uint8, (CAM_HEIGHT,CAM_WIDTH))
    ])

    dt_downsampled_uint8_RGB = np.dtype([
        ('index', int, (1,)),
        ('timestamp', float, (1,)), 
        ('image', np.uint8, (round(CAM_HEIGHT*t.downsample_fullres_export), round(CAM_WIDTH*t.downsample_fullres_export), 3))
    ])


    def serialize_image(buffer: NDArray, obj: Tuple[int, float, NDArray]) -> None:
        #tic = time.monotonic_ns()
        #buffer[:] = obj # this is slower, why ?
        index, timestamp, image = obj 
        buffer['index'] = index
        buffer['timestamp'] = timestamp
        buffer['image'] = image
        #print(buffer.dtype, 1e-6*(time.monotonic_ns() - tic))

    def deserialize_image(arr: NDArray) -> Tuple[int, float, NDArray]:
        index = arr['index'].item()
        timestamp = arr['timestamp'].item()
        image = arr[0]['image']
        return (index, timestamp, image)

    q_cam = MonitoredQueue(
        ObjectRingBuffer2(
            num_items = 100,
            data_type = dt_uint8_gray,
            serialize = serialize_image,
            deserialize = deserialize_image,
            logger = queue_logger,
            name = 'camera_to_background',
            t_refresh=T_REFRESH
        )
    )

    q_save_image = MonitoredQueue(
        ObjectRingBuffer2(
            num_items = 100,
            data_type = dt_uint8_gray,
            serialize = serialize_image,
            deserialize = deserialize_image,
            logger = queue_logger,
            name = 'camera_to_image_saver',
            t_refresh=T_REFRESH
        )
    )

    q_display = MonitoredQueue(
        ObjectRingBuffer2(
            num_items = 100,
            data_type = dt_downsampled_uint8_RGB,
            serialize = serialize_image,
            deserialize = deserialize_image,
            logger = queue_logger,
            name = 'overlay_to_display',
            t_refresh=T_REFRESH
        )
    )


    # ring buffer background ------------------------------------------------------------------
    # IMPORTANT: need to copy the data out of the 
    # circular buffer otherwise it can be modified after the fact
    # set copy=True
    
    dt_single_gray = np.dtype([
        ('index', int, (1,)),
        ('timestamp', float, (1,)), 
        ('image', np.float32, (CAM_HEIGHT,CAM_WIDTH))
    ])

    q_back = MonitoredQueue(
        ObjectRingBuffer2(
            num_items = 100,
            data_type = dt_single_gray,
            serialize = serialize_image,
            deserialize = deserialize_image,
            copy=False, # you probably don't need to copy if processing is fast enough
            logger = queue_logger,
            name = 'background_to_trackers',
            t_refresh=T_REFRESH
        )
    )

    q_camera_control = QueueMP()
    q_camera_info = QueueMP()

    # tracking ring buffer -------------------------------------------------------------------
    # get dtype and itemsize for tracker results
    tracking = t.track(np.zeros((CAM_HEIGHT,CAM_WIDTH), dtype=np.float32))
    arr_multifish = tracking.to_numpy()

    dt_tracking_multifish = np.dtype([
        ('index', int, (1,)),
        ('timestamp', float, (1,)), 
        ('tracking', arr_multifish.dtype, (1,))
    ])

    def serialize_tracking_multifish(buffer: NDArray, obj: Tuple[int, float, MultiFishTracking]) -> NDArray:
        #tic = time.monotonic_ns()
        index, timestamp, tracking = obj
        buffer['index'] = index
        buffer['timestamp'] = timestamp
        tracking.to_numpy(buffer['tracking'])
        #buffer['tracking'] = tracking.to_numpy() # maybe it should be tracking.to_numpy(array_to_copy_into) to write directly to the buffer. Rewrite function as tracking(out: Optional[NDArray] = None)
        #print(buffer.dtype, 1e-6*(time.monotonic_ns() - tic))


    def deserialize_tracking_multifish(arr: NDArray) -> Tuple[int, float, MultiFishTracking]:
        index = arr['index'].item()
        timestamp = arr['timestamp'].item()
        tracking = MultiFishTracking.from_numpy(arr[0]['tracking'][0])
        return (index, timestamp, tracking)

    # ---
    dt_tracking_body = np.dtype([
        ('index', int, (1,)),
        ('timestamp', float, (1,)), 
        ('centroid', np.float32, (1,2)),
        ('heading', np.float32, (2,))
    ])

    def serialize_tracking_body(buffer: NDArray, obj: Tuple[int, float, NDArray, NDArray]) -> NDArray:
        index, timestamp, centroid, heading = obj
        buffer['index'] = index
        buffer['timestamp'] = timestamp
        buffer['centroid'] = centroid
        buffer['heading'] = heading

    def deserialize_tracking_body(arr: NDArray) -> Tuple[int, float, NDArray, NDArray]:
        index = arr['index'].item()
        timestamp = arr['timestamp'].item()
        centroid = arr[0]['centroid']
        heading = arr[0]['heading']
        return (index, timestamp, centroid, heading)

    q_tracking = MonitoredQueue(
        ObjectRingBuffer2(
            num_items = 100,
            data_type = dt_tracking_body,
            serialize = serialize_tracking_body,
            deserialize = deserialize_tracking_body,
            logger = queue_logger,
            name = 'tracker_to_phototaxis',
            t_refresh=T_REFRESH
        )
    )

    q_overlay = MonitoredQueue(
        ObjectRingBuffer2(
            num_items = 100,
            data_type = dt_tracking_multifish,
            serialize = serialize_tracking_multifish,
            deserialize = deserialize_tracking_multifish,
            logger = queue_logger,
            name = 'tracker_to_overlay',
            t_refresh=T_REFRESH
        )
    )

    dag = ProcessingDAG()

    # data
    for i in range(N_BACKGROUND_WORKERS):   
        dag.connect_data(sender=cam, receiver=bckg[i], queue=q_cam, name='background_subtraction')
    
    # NOTE: the order in which you declare connections matter: background_subtraction will
    # be served before image_saver
    if RECORD_VIDEO:
        dag.connect_data(sender=cam, receiver=image_saver, queue=q_save_image, name='image_saver')

    for i in range(N_BACKGROUND_WORKERS):
        for j in range(N_TRACKER_WORKERS):
            dag.connect_data(sender=bckg[i], receiver=trck[j], queue=q_back, name='background_subtracted')

    for i in range(N_TRACKER_WORKERS):
        dag.connect_data(sender=trck[i], receiver=stim, queue=q_tracking, name='stimulus')
        dag.connect_data(sender=trck[i], receiver=oly, queue=q_overlay, name='overlay')

    dag.connect_data(sender=oly, receiver=dis, queue=q_display, name='disp')

    # metadata
    dag.connect_metadata(sender=cam_control, receiver=cam, queue=q_camera_control, name='camera_control')
    dag.connect_metadata(sender=cam, receiver=cam_control, queue=q_camera_info, name='camera_info')

    worker_logger.start()
    queue_logger.start()
    dag.start()
    time.sleep(DURATION_S)
    dag.stop()
    queue_logger.stop()
    worker_logger.stop()

    print('cam to background', q_cam.get_average_freq(), q_cam.queue.num_lost_item.value)
    if RECORD_VIDEO:
        print('cam to image saver', q_save_image.get_average_freq(), q_save_image.queue.num_lost_item.value)
    print('background to trackers', q_back.get_average_freq(), q_back.queue.num_lost_item.value)
    print('trackers to visual stim', q_tracking.get_average_freq(), q_tracking.queue.num_lost_item.value)
    print('trackers to overlay', q_overlay.get_average_freq(), q_overlay.queue.num_lost_item.value)
    print('overlay to display', q_display.get_average_freq(), q_display.queue.num_lost_item.value)

    #plot_worker_logs(LOGFILE_WORKERS, outlier_thresh=1000)
    # NOTE: if you have more worker than necessary, you will see a heavy tail in the receive time.
    # This is perfectly normal, each tracker may be skip a few cycles if the others are already 
    # filling the job
    # NOTE: send time = serialization (one copy) + writing (one copy) and acquiring lock
    # NOTE: receive time = deserialization + reading (sometimes one copy) from queue and acquiring lock
    # NOTE: check that total_time/#workers is <= to cam for all workers (except workers with reduced fps like display)

    # NOTE: the intial delay at the level of the tracker (~500ms), is most likely due to numba. When I remove the 
    # tail tracker, the latency goes way down at the beginning. Maybe I can force the tracker to compile during initialization ?


    #plot_queue_logs(LOGFILE_QUEUES)
    # NOTE: memory bandwidth ~10GB/s. 1800x1800x3 uint8 = 9.3 MB, 1800x1800 float32 = 12.4 MB
    # camera: creation, serialization, put on buffer
    # background: creation, serialization, put on buffer
    # tracker: serialization, put on buffer

    # with larger image, bottleneck transition from CPU to memory bandwidth ?
    