from multiprocessing import set_start_method

# This is apparently very important to set. Otherwise OpenCV warpAffine
# takes way to much time when run in a separate process
import os
os.environ["OMP_NUM_THREADS"] = "1"

import numpy as np
from numpy.typing import NDArray
from typing import Tuple
import json
from PyQt5.QtWidgets import QApplication

from gui import MainGui
from multiprocessing_logger import Logger
from ipc_tools import MonitoredQueue, ObjectRingBuffer2, QueueMP
from video_tools import BackroundImage
from dagline import receive_strategy, send_strategy
from stimulus import VisualStimWorker, GeneralStim
from tracker import (
    GridAssignment, 
    MultiFishTracker_CPU,
    MultiFishOverlay_opencv, 
    MultiFishTracking,
    AnimalTracker_CPU, 
    AnimalOverlay_opencv, 
    AnimalTrackerParamTracking, 
    AnimalTrackerParamOverlay, 
    BodyTracker_CPU, 
    BodyOverlay_opencv, 
    BodyTrackerParamTracking, 
    BodyTrackerParamOverlay,  
)
from workers import (
    BackgroundSubWorker, 
    CameraWorker, 
    DisplayWorker, 
    TrackerWorker, 
    OverlayWorker, 
    ImageSaverWorker, 
    CameraGui, 
    TrackerGui, 
    StimGUI,
    TrackingDisplay
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
    PHOTOTAXIS_POLARITY,
    OMR_SPATIAL_PERIOD_MM,
    OMR_ANGLE_DEG,
    OMR_SPEED_MM_PER_SEC,
    OKR_SPATIAL_FREQUENCY_DEG,
    OKR_SPEED_DEG_PER_SEC,
    LOOMING_CENTER_MM,
    LOOMING_PERIOD_SEC,
    LOOMING_EXPANSION_TIME_SEC,
    LOOMING_EXPANSION_SPEED_MM_PER_SEC,
    FOREGROUND_COLOR, 
    BACKGROUND_COLOR, 
)

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
        omr_spatial_period_mm = OMR_SPATIAL_PERIOD_MM,
        omr_angle_deg = OMR_ANGLE_DEG,
        omr_speed_mm_per_sec = OMR_SPEED_MM_PER_SEC,
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
        phototaxis_polarity = PHOTOTAXIS_POLARITY,
        omr_spatial_period_mm = OMR_SPATIAL_PERIOD_MM,
        omr_angle_deg = OMR_ANGLE_DEG,
        omr_speed_mm_per_sec = OMR_SPEED_MM_PER_SEC,
        okr_spatial_frequency_deg = OKR_SPATIAL_FREQUENCY_DEG,
        okr_speed_deg_per_sec = OKR_SPEED_DEG_PER_SEC,
        looming_center_mm = LOOMING_CENTER_MM,
        looming_period_sec = LOOMING_PERIOD_SEC,
        looming_expansion_time_sec = LOOMING_EXPANSION_TIME_SEC,
        looming_expansion_speed_mm_per_sec = LOOMING_EXPANSION_SPEED_MM_PER_SEC,
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
        animal_tracking_param=ANIMAL_TRACKING_PARAM,
        body_tracking_param=BODY_TRACKING_PARAM,
        n_tracker_workers=N_TRACKER_WORKERS,
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
                cam_width=CAM_WIDTH,
                cam_height=CAM_HEIGHT,
                n_tracker_workers=N_TRACKER_WORKERS,
                name=f'tracker{i}', 
                logger=worker_logger, 
                logger_queues=queue_logger, 
                send_data_strategy=send_strategy.BROADCAST, 
                receive_data_timeout=1.0, 
                profile=False
            )
        )

    trck_disp = TrackingDisplay(
        overlay=o, 
        fps=30, 
        name="tracking_display", 
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
        'tracking_display': trck_disp,
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
        'tracker_to_tracking_display': q_overlay,
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
