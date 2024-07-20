from multiprocessing import set_start_method, Process

# This is apparently very important to set. Otherwise OpenCV warpAffine
# takes way to much time when run in a separate process
import os
os.environ["OMP_NUM_THREADS"] = "1"

from tracker import (
    GridAssignment, MultiFishTracker, MultiFishTracker_CPU, MultiFishOverlay, MultiFishOverlay_opencv, MultiFishTracking,
    AnimalTracker_CPU, AnimalOverlay_opencv, AnimalTrackerParamTracking, AnimalTrackerParamOverlay, 
    BodyTracker_CPU, BodyOverlay_opencv, BodyTrackerParamTracking, BodyTrackerParamOverlay,  
)
from multiprocessing_logger import Logger
from ipc_tools import MonitoredQueue, ObjectRingBuffer2, QueueMP
from video_tools import BackroundImage
from dagline import receive_strategy, send_strategy, ProcessingDAG
from stimulus import VisualStimWorker, GeneralStim

import subprocess
import numpy as np
from numpy.typing import NDArray
import time
from typing import Dict, Tuple
import json

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QPushButton
from qt_widgets import LabeledEditLine, LabeledSpinBox

from workers import (
    BackgroundSubWorker, CameraWorker, DisplayWorker, TrackerWorker, OverlayWorker, ImageSaverWorker, 
    CameraGui, TrackerGui, StimGUI
)

from config import (
    REGISTRATION_FILE, 
    CAM_WIDTH, 
    CAM_HEIGHT,
    CAM_EXPOSURE_MS, 
    CAM_GAIN, 
    CAM_FPS,
    CAM_OFFSETX, 
    CAM_OFFSETY, 
    PROJ_WIDTH, 
    PROJ_HEIGHT, 
    PROJ_POS, 
    PROJ_FPS,
    PIXEL_SCALING, 
    PIX_PER_MM,
    BACKGROUND_FILE, 
    IMAGE_FOLDER,
    ANIMAL_TRACKING_PARAM,
    BODY_TRACKING_PARAM, 
    CAMERA_CONSTRUCTOR,
    LOGFILE_WORKERS, 
    LOGFILE_QUEUES,
    BACKGROUND_POLARITY,
    N_BACKGROUND_WORKERS, 
    N_TRACKER_WORKERS,
    BACKGROUND_GPU, 
    T_REFRESH, 
    RECORD_VIDEO,
    PHOTOTAXIS_POLARITY,
    OMR_SPATIAL_FREQUENCY_DEG,
    OMR_ANGLE_DEG,
    OMR_SPEED_DEG_PER_SEC,
    OKR_SPATIAL_FREQUENCY_DEG,
    OKR_SPEED_DEG_PER_SEC,
    LOOMING_CENTER_MM,
    LOOMING_PERIOD_SEC,
    LOOMING_EXPANSION_TIME_SEC,
    LOOMING_EXPANSION_SPEED_MM_PER_SEC,
    FOREGROUND_COLOR, 
    BACKGROUND_COLOR, 
)

class MainGui(QWidget):
    
    def __init__(self, workers: Dict, queues: Dict, worker_logger: Logger, queue_logger: Logger, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.dag = None
        self.workers = workers
        self.queues = queues
        self.worker_logger = worker_logger
        self.queue_logger = queue_logger
        self.setWindowTitle('Main controls')
        self.create_components()
        self.layout_components()

    def create_dag(self):

        # clear workers and queues

        for key, worker in self.workers.items():
            worker.reset()

        for key, queue in self.queues.items():
            queue.clear()

        self.dag = ProcessingDAG()

        # data
        for i in range(N_BACKGROUND_WORKERS):   
            self.dag.connect_data(
                sender=self.workers['camera'], 
                receiver=self.workers[f'background_{i}'], 
                queue=self.queues['camera_to_background'], 
                name='background_subtraction'
            )
        
        # NOTE: the order in which you declare connections matter: background_subtraction will
        # be served before image_saver
        if RECORD_VIDEO:
            self.dag.connect_data(
                sender=self.workers['camera'], 
                receiver=self.workers['video_recorder'], 
                queue=self.queues['camera_to_video_recorder'], 
                name='image_saver'
            )

        for i in range(N_BACKGROUND_WORKERS):
            for j in range(N_TRACKER_WORKERS):
                self.dag.connect_data(
                    sender=self.workers[f'background_{i}'], 
                    receiver=self.workers[f'tracker_{j}'], 
                    queue=self.queues['background_to_tracker'], 
                    name='background_subtracted'
                )

        self.dag.connect_data(
            sender=self.workers['overlay'], 
            receiver=self.workers['display'], 
            queue=self.queues['overlay_to_display'], 
            name='disp'
        )

        for i in range(N_TRACKER_WORKERS):
            self.dag.connect_data(
                sender=self.workers[f'tracker_{i}'], 
                receiver=self.workers['overlay'], 
                queue=self.queues['tracker_to_overlay'], 
                name='overlay'
            )

        for i in range(N_TRACKER_WORKERS):
            self.dag.connect_data(
                sender=self.workers[f'tracker_{i}'], 
                receiver=self.workers['visual_stim'], 
                queue=self.queues['tracker_to_stim'], 
                name='stimulus'
            )

        # metadata
        self.dag.connect_metadata(
            sender=self.workers['camera_gui'], 
            receiver=self.workers['camera'], 
            queue=self.queues['camera_control_to_camera'], 
            name='camera_control'
        )
        
        self.dag.connect_metadata(
            sender=self.workers['camera'], 
            receiver=self.workers['camera_gui'], 
            queue=self.queues['camera_to_camera_control'], 
            name='camera_info'
        )

        self.dag.connect_metadata(
            sender=self.workers['visual_stim_control'], 
            receiver=self.workers['visual_stim'], 
            queue=self.queues['visual_stim_control'], 
            name='visual_stim_control'
        )
        
        for i in range(N_TRACKER_WORKERS):
            self.dag.connect_metadata(
                sender=self.workers['tracker_gui'], 
                receiver=self.workers[f'tracker_{i}'], 
                queue=self.queues[f'tracker_control_to_tracker_{i}'], 
                name=f'tracker_control_{i}'
            )

    def create_components(self):
        
        # calibration
        self.registration_button = QPushButton()
        self.registration_button.setText('registration')
        self.registration_button.clicked.connect(self.registration)

        self.check_registration_button = QPushButton()
        self.check_registration_button.setText('check registration')
        self.check_registration_button.clicked.connect(self.check_registration)

        self.pixel_size_button = QPushButton()
        self.pixel_size_button.setText('get pix/mm')
        self.pixel_size_button.clicked.connect(self.get_pix_per_mm)

        self.check_pixel_size_button = QPushButton()
        self.check_pixel_size_button.setText('check pix/mm')
        self.check_pixel_size_button.clicked.connect(self.check_pix_per_mm)

        self.label_method = QLabel()
        self.label_method.setText('Background type:')
        self.background_method = QComboBox()
        self.background_method.addItem('static')
        self.background_method.addItem('inpaint')

        self.background_button = QPushButton()
        self.background_button.setText('background')
        self.background_button.clicked.connect(self.background)

        # experiment
        self.fish_id = LabeledSpinBox()
        self.fish_id.setText('Fish ID:')
        self.fish_id.setValue(0)
        self.fish_id.valueChanged.connect(self.experiment_data)

        self.dpf = LabeledSpinBox()
        self.dpf.setText('Fish age (dpf):')
        self.dpf.setValue(7)
        self.dpf.valueChanged.connect(self.experiment_data)

        self.duration = LabeledSpinBox()
        self.duration.setText('rec. duration (s)')
        self.duration.setValue(60)
        self.duration.valueChanged.connect(self.experiment_data)

        self.filename = LabeledEditLine()
        self.filename.setLabel('result file:')
        
        self.start_button = QPushButton()
        self.start_button.setText('start')
        self.start_button.clicked.connect(self.start)

        self.stop_button = QPushButton()
        self.stop_button.setText('stop')
        self.stop_button.clicked.connect(self.stop)

        self.record_button = QPushButton()
        self.record_button.setText('record')
        self.record_button.clicked.connect(self.record)

    def layout_components(self):
        
        controls = QHBoxLayout()
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        controls.addWidget(self.record_button)

        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(self.registration_button)
        layout.addWidget(self.check_registration_button)
        layout.addWidget(self.pixel_size_button)
        layout.addWidget(self.check_pixel_size_button)
        layout.addWidget(self.label_method)
        layout.addWidget(self.background_method)
        layout.addWidget(self.background_button)
        layout.addWidget(self.fish_id)
        layout.addWidget(self.dpf)
        layout.addWidget(self.duration)
        layout.addWidget(self.filename)
        layout.addLayout(controls)
        layout.addStretch()

    def experiment_data(self):
        pass

    def registration(self):
        subprocess.Popen(['python', 'ZebVR/calibration/registration.py'])

    def check_registration(self):
        subprocess.Popen(['python', 'ZebVR/calibration/check_registration.py'])

    def background(self):
        if self.background_method.currentText() == 'inpaint':
            subprocess.Popen(['python', 'ZebVR/background/inpaint_background.py'])
        elif self.background_method.currentText() == 'static':
            subprocess.Popen(['python', 'ZebVR/background/static_background.py'])

    def get_pix_per_mm(self):
        subprocess.Popen(['python', 'ZebVR/calibration/pix_per_mm.py'])

    def check_pix_per_mm(self):
        subprocess.Popen(['python', 'ZebVR/calibration/check_pix_per_mm.py'])
    
    def start(self):
        self.create_dag()
        self.p_worker_logger = Process(target=self.worker_logger.run)
        self.p_queue_logger = Process(target=self.queue_logger.run)
        self.p_worker_logger.start()
        self.p_queue_logger.start()
        print('Starting DAG')
        self.dag.start()

    def stop(self):
        self.dag.stop()
        print('cam to background', self.queues['camera_to_background'].get_average_freq(), self.queues['camera_to_background'].queue.num_lost_item.value)
        if RECORD_VIDEO:
            print('cam to image saver', self.queues['camera_to_video_recorder'].get_average_freq(), self.queues['camera_to_video_recorder'].queue.num_lost_item.value)
        print('background to trackers', self.queues['background_to_tracker'].get_average_freq(), self.queues['background_to_tracker'].queue.num_lost_item.value)
        print('trackers to visual stim', self.queues['tracker_to_stim'].get_average_freq(), self.queues['tracker_to_stim'].queue.num_lost_item.value)
        print('trackers to overlay', self.queues['tracker_to_overlay'].get_average_freq(), self.queues['tracker_to_overlay'].queue.num_lost_item.value)
        print('overlay to display', self.queues['overlay_to_display'].get_average_freq(), self.queues['overlay_to_display'].queue.num_lost_item.value)
        self.worker_logger.stop()
        self.queue_logger.stop()
        self.p_worker_logger.join()
        self.p_queue_logger.join()
        print('DAG stopped')

    def record(self):
        self.start()
        time.sleep(self.duration.value())
        self.stop()

## numpy array serialization / deserialization functions

def serialize_image(buffer: NDArray, obj: Tuple[int, float, NDArray]) -> None:
    index, timestamp, image = obj 
    buffer['index'] = index
    buffer['timestamp'] = timestamp
    buffer['image'] = image

def deserialize_image(arr: NDArray) -> Tuple[int, float, NDArray]:
    index = arr['index'].item()
    timestamp = arr['timestamp'].item()
    image = arr[0]['image']
    return (index, timestamp, image)

def serialize_tracking_multifish(buffer: NDArray, obj: Tuple[int, float, MultiFishTracking]) -> NDArray:
    index, timestamp, tracking = obj
    buffer['index'] = index
    buffer['timestamp'] = timestamp
    tracking.to_numpy(buffer['tracking'])

def deserialize_tracking_multifish(arr: NDArray) -> Tuple[int, float, MultiFishTracking]:
    index = arr['index'].item()
    timestamp = arr['timestamp'].item()
    tracking = MultiFishTracking.from_numpy(arr[0]['tracking'][0])
    return (index, timestamp, tracking)

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

if __name__ == "__main__":

    set_start_method('spawn')

    try:
        with open(REGISTRATION_FILE, 'r') as f:
            calibration = json.load(f)
    except FileNotFoundError:
        print('Registration file not found, please run calibration first')
        calibration = {}
        calibration['cam_to_proj'] = [[1,0,0],[0,1,0],[0,0,1]]
        calibration['proj_to_cam'] = [[1,0,0],[0,1,0],[0,0,1]]

    worker_logger = Logger(LOGFILE_WORKERS, Logger.INFO)
    queue_logger = Logger(LOGFILE_QUEUES, Logger.INFO)

    ## Declare workers -----------------------------------------------------------------------------

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

    b = BackroundImage(
        image_file_name = BACKGROUND_FILE,
        polarity = BACKGROUND_POLARITY,
        use_gpu = BACKGROUND_GPU
    )
    
    stim = GeneralStim(
        window_size=(PROJ_WIDTH, PROJ_HEIGHT),
        window_position=PROJ_POS,
        foreground_color=FOREGROUND_COLOR,
        background_color=BACKGROUND_COLOR,
        window_decoration=False,
        transformation_matrix=np.array(calibration['cam_to_proj'], dtype=np.float32),
        pixel_scaling=PIXEL_SCALING,
        pix_per_mm= PIX_PER_MM,
        refresh_rate=PROJ_FPS,
        vsync=True,
        timings_file = 'display_timings.csv',
        stim_select = 0,
        phototaxis_polarity = PHOTOTAXIS_POLARITY,
        omr_spatial_frequency_deg = OMR_SPATIAL_FREQUENCY_DEG,
        omr_angle_deg = OMR_ANGLE_DEG,
        omr_speed_deg_per_sec = OMR_SPEED_DEG_PER_SEC,
        okr_spatial_frequency_deg = OKR_SPATIAL_FREQUENCY_DEG,
        okr_speed_deg_per_sec = OKR_SPEED_DEG_PER_SEC,
        looming_center_mm = LOOMING_CENTER_MM,
        looming_period_sec = LOOMING_PERIOD_SEC,
        looming_expansion_time_sec = LOOMING_EXPANSION_TIME_SEC,
        looming_expansion_speed_mm_per_sec = LOOMING_EXPANSION_SPEED_MM_PER_SEC
    )

    stim_worker = VisualStimWorker(
        stim=stim, 
        name='visual_stim', 
        logger=worker_logger, 
        logger_queues=queue_logger, 
        receive_data_timeout=1.0
    )

    stim_control = StimGUI(
        name='stim_gui', 
        logger=worker_logger, 
        logger_queues=queue_logger, 
        receive_data_timeout=1.0
    ) 

    cam_control = CameraGui(
        name='cam_gui',  
        logger=worker_logger, 
        logger_queues=queue_logger,
        receive_data_timeout=1.0
    )

    tracker_control = TrackerGui(
        name='tracker_gui',  
        logger=worker_logger, 
        logger_queues=queue_logger,
        receive_data_timeout=1.0   
    )
    
    cam = CameraWorker(
        camera_constructor = CAMERA_CONSTRUCTOR, 
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

    image_saver = ImageSaverWorker(
        folder = IMAGE_FOLDER, 
        name='image_saver',  
        logger=worker_logger, 
        logger_queues=queue_logger, 
        receive_data_timeout=1.0
    )

    bckg = []
    for i in range(N_BACKGROUND_WORKERS):
        bckg.append(
            BackgroundSubWorker(
                b, 
                name=f'background{i}', 
                logger=worker_logger, 
                logger_queues=queue_logger, 
                receive_data_timeout=1.0, 
                profile=False
            )
        )

    trck = []
    for i in range(N_TRACKER_WORKERS):
        trck.append(
            TrackerWorker(
                t, 
                name=f'tracker{i}', 
                logger=worker_logger, 
                logger_queues=queue_logger, 
                send_data_strategy=send_strategy.BROADCAST, 
                receive_data_timeout=1.0, 
                profile=False
            )
        )

    dis = DisplayWorker(
        fps=30, 
        name='display', 
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

    ## Declare queues -----------------------------------------------------------------------------

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
        
    dt_single_gray = np.dtype([
        ('index', int, (1,)),
        ('timestamp', float, (1,)), 
        ('image', np.float32, (CAM_HEIGHT,CAM_WIDTH))
    ])

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

    # tracking ring buffer -------------------------------------------------------------------
    # get dtype and itemsize for tracker results
    tracking = t.track(np.zeros((CAM_HEIGHT,CAM_WIDTH), dtype=np.float32))
    arr_multifish = tracking.to_numpy()

    dt_tracking_multifish = np.dtype([
        ('index', int, (1,)),
        ('timestamp', float, (1,)), 
        ('tracking', arr_multifish.dtype, (1,))
    ])

    # ---
    dt_tracking_body = np.dtype([
        ('index', int, (1,)),
        ('timestamp', float, (1,)), 
        ('centroid', np.float32, (2,)),
        ('heading', np.float32, (2,2))
    ])

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

    ## DAG ----------------------------------------------------------------------

    workers = {
        'camera': cam,
        'video_recorder': image_saver,
        'visual_stim': stim_worker,
        'overlay': oly,
        'display': dis,
        'camera_gui': cam_control,
        'visual_stim_control': stim_control,
        'tracker_gui': tracker_control
    }
    for i in range(N_TRACKER_WORKERS):
        workers[f'tracker_{i}'] = trck[i]
    for i in range(N_BACKGROUND_WORKERS):
        workers[f'background_{i}'] = bckg[i]
        
    queues = {
        'camera_to_background': q_cam,
        'camera_to_video_recorder': q_save_image,
        'background_to_tracker': q_back,
        'tracker_to_stim': q_tracking,
        'tracker_to_overlay': q_overlay,
        'overlay_to_display': q_display,
        'camera_control_to_camera': QueueMP(),
        'camera_to_camera_control': QueueMP(),
        'visual_stim_control': QueueMP()
    }
    for i in range(N_TRACKER_WORKERS):
        queues[f'tracker_control_to_tracker_{i}'] = QueueMP()

    app = QApplication([])
    main = MainGui(workers=workers, queues=queues, worker_logger=worker_logger, queue_logger=queue_logger)
    main.show()
    app.exec_()
