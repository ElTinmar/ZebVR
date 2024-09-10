from multiprocessing import set_start_method

# This is apparently very important to set. Otherwise OpenCV warpAffine
# takes way to much time when run in a separate process
# NOTE setting to low value but not necessarily 1 ?
import os
os.environ["OMP_NUM_THREADS"] = "1"
#os.environ["OPENBLAS_NUM_THREADS"] = "1"
#os.environ["MKL_NUM_THREADS"] = "1"
#os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
#os.environ["NUMEXPR_NUM_THREADS"] = "1"

from pathlib import Path
import numpy as np
from numpy.typing import NDArray
from typing import Tuple
import json
from PyQt5.QtWidgets import QApplication

from ZebVR.gui import MainGui
from multiprocessing_logger import Logger
from ipc_tools import MonitoredQueue, ModifiableRingBuffer, QueueMP
from video_tools import BackroundImage
from dagline import receive_strategy, send_strategy
from ZebVR.stimulus import VisualStimWorker, GeneralStim
from tracker import (
    GridAssignment, 
    MultiFishTracker_CPU,
    MultiFishOverlay_opencv, 
    MultiFishTrackerParamTracking,
    MultiFishTrackerParamOverlay,
    AnimalTracker_CPU, 
    AnimalOverlay_opencv, 
    AnimalTrackerParamTracking, 
    AnimalTrackerParamOverlay, 
    BodyOverlay_opencv, 
    BodyTrackerParamOverlay,  
    EyesOverlay_opencv,
    EyesTrackerParamOverlay,
    TailOverlay_opencv,
    TailTrackerParamOverlay,
)
from ZebVR.workers import (
    BackgroundSubWorker, 
    CameraWorker, 
    TrackerWorker, 
    DummyTrackerWorker,
    ImageSaverWorker, 
    CameraGui, 
    TrackerGui, 
    StimGUI,
    TrackingDisplay,
    Protocol
)
from ZebVR.config import (
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
    VIDEO_RECORDING_FPS,
    VIDEO_RECORDING_COMPRESSION,
    VIDEO_RECORDING_RESIZE,
    CAMERA_CONSTRUCTOR,
    LOGFILE_WORKERS, 
    LOGFILE_QUEUES,
    DISPLAY_FPS,
    DOWNSAMPLE_TRACKING_EXPORT,
    BACKGROUND_POLARITY,
    N_BACKGROUND_WORKERS, 
    N_TRACKER_WORKERS,
    BACKGROUND_GPU, 
    T_REFRESH, 
    OPEN_LOOP,
    OPEN_LOOP_DATAFILE,
    N_PTS_INTERP
)

if __name__ == "__main__":

    set_start_method('spawn')

    try:
        with open(REGISTRATION_FILE, 'r') as f:
            calibration = json.load(f)
    except FileNotFoundError:
        print('Registration file not found, please run calibration first')
        calibration = {}
        calibration['cam_to_proj'] = [[1,0,0],[0,-1,504],[0,0,1]]
        calibration['proj_to_cam'] = [[1,0,0],[0,-1,-504],[0,0,1]]

    worker_logger = Logger(LOGFILE_WORKERS, Logger.INFO)
    queue_logger = Logger(LOGFILE_QUEUES, Logger.INFO)

    ## Declare workers -----------------------------------------------------------------------------

    tracker_control = TrackerGui(
        n_tracker_workers=N_TRACKER_WORKERS,
        name='tracker_gui',  
        logger=worker_logger, 
        logger_queues=queue_logger,
        receive_data_timeout=1.0   
    )

    o = MultiFishOverlay_opencv(
        MultiFishTrackerParamOverlay(
            AnimalOverlay_opencv(AnimalTrackerParamOverlay()),
            BodyOverlay_opencv(BodyTrackerParamOverlay()),
            EyesOverlay_opencv(EyesTrackerParamOverlay()),
            TailOverlay_opencv(TailTrackerParamOverlay())
        )
    )

    t = MultiFishTracker_CPU(
        MultiFishTrackerParamTracking(
            accumulator=None,
            animal=AnimalTracker_CPU(
                assignment=GridAssignment(LUT=np.zeros((CAM_HEIGHT,CAM_WIDTH), dtype=np.int_)), 
                tracking_param=AnimalTrackerParamTracking(source_image_shape=(CAM_HEIGHT,CAM_WIDTH))
            ),
            body=None, 
            eyes=None, 
            tail=None
        )
    )

    b = BackroundImage(
        image_file_name = BACKGROUND_FILE,
        polarity = BACKGROUND_POLARITY,
        use_gpu = BACKGROUND_GPU
    )
    
    stim = GeneralStim(
        window_size=(PROJ_WIDTH, PROJ_HEIGHT),
        window_position=PROJ_POS,
        window_decoration=False,
        transformation_matrix=np.array(calibration['cam_to_proj'], dtype=np.float32),
        pixel_scaling=PIXEL_SCALING,
        pix_per_mm= PIX_PER_MM,
        refresh_rate=PROJ_FPS,
        vsync=True,
        timings_file = 'display_timings.csv',
        stim_select = 0,
        num_tail_points_interp = N_PTS_INTERP,
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
        fps = VIDEO_RECORDING_FPS,
        compress= VIDEO_RECORDING_COMPRESSION,
        resize=VIDEO_RECORDING_RESIZE,
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
        if OPEN_LOOP:
            trck.append(
                DummyTrackerWorker(
                    None, #TODO fix that
                    name=f'tracker{i}', 
                    logger=worker_logger, 
                    logger_queues=queue_logger, 
                    send_data_strategy=send_strategy.BROADCAST, 
                    receive_data_timeout=1.0, 
                    profile=False
                )
            )
        else:
            trck.append(
                TrackerWorker(
                    t, 
                    cam_width=CAM_WIDTH,
                    cam_height=CAM_HEIGHT,
                    n_tracker_workers=N_TRACKER_WORKERS,
                    downsample_tracker_export=DOWNSAMPLE_TRACKING_EXPORT,
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
        fps=DISPLAY_FPS, 
        name="tracking_display", 
        logger=worker_logger, 
        logger_queues=queue_logger, 
        receive_data_timeout=1.0
    )

    protocol = Protocol(
        name="protocol", 
        logger=worker_logger, 
        logger_queues=queue_logger, 
        receive_data_timeout=1.0
    )

    ## Declare queues -----------------------------------------------------------------------------
    
    q_cam = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            logger = queue_logger,
            name = 'camera_to_background',
            t_refresh=T_REFRESH
        )
    )

    q_save_image = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
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
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            copy=False, # you probably don't need to copy if processing is fast enough
            logger = queue_logger,
            name = 'background_to_trackers',
            t_refresh=T_REFRESH
        )
    )

    # ---
    q_tracking = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            logger = queue_logger,
            name = 'tracker_to_stim',
            t_refresh=T_REFRESH
        )
    )

    q_overlay = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            logger = queue_logger,
            name = 'tracker_to_overlay',
            t_refresh=T_REFRESH
        )
    )

    ## DAG for closed loop ----------------------------------------------------------------------

    workers = {
        'camera': cam,
        'video_recorder': image_saver,
        'visual_stim': stim_worker,
        'tracking_display': trck_disp,
        'camera_gui': cam_control,
        'visual_stim_control': stim_control,
        'protocol': protocol,
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
