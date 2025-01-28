from typing import Dict, Optional, Tuple
import numpy as np

from multiprocessing_logger import Logger
from ipc_tools import MonitoredQueue, ModifiableRingBuffer, QueueMP
from video_tools import BackroundImage, Polarity
from dagline import ProcessingDAG, receive_strategy, send_strategy
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
    BodyTracker_CPU,
    BodyOverlay_opencv, 
    BodyTrackerParamOverlay,
    BodyTrackerParamTracking,
    EyesTracker_CPU,  
    EyesOverlay_opencv,
    EyesTrackerParamOverlay,
    EyesTrackerParamTracking,
    TailTracker_CPU,
    TailOverlay_opencv,
    TailTrackerParamOverlay,
    TailTrackerParamTracking
)
from ZebVR.workers import (
    BackgroundSubWorker, 
    CameraWorker, 
    TrackerWorker, 
    TrackerGui, 
    TrackingDisplay,
    QueueMonitor,
    TrackingSaver
)

def tracking(settings: Dict, dag: Optional[ProcessingDAG] = None) -> Tuple[ProcessingDAG, Logger, Logger]:
    
    # create DAG
    if dag is None:
        dag = ProcessingDAG()
    
    # create loggers
    worker_logger = Logger(settings['output']['worker_logfile'], Logger.INFO)
    queue_logger = Logger(settings['output']['queue_logfile'], Logger.INFO)

    # create queues -----------------------------------------------------------------------            
    queue_cam = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2, # TODO add a widget for that?
            logger = queue_logger,
            name = 'camera_to_background',
            t_refresh = 1e-6 * settings['vr_settings']['queue_refresh_time_microsec']
        )
    )

    queue_background = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            logger = queue_logger,
            name = 'background_to_trackers',
            t_refresh = 1e-6 * settings['vr_settings']['queue_refresh_time_microsec']
        )
    )

    queue_tracking = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            logger = queue_logger,
            name = 'tracker_to_stim',
            t_refresh = 1e-6 * settings['vr_settings']['queue_refresh_time_microsec']
        )
    )

    queue_overlay = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            logger = queue_logger,
            name = 'tracker_to_overlay',
            t_refresh = 1e-6 * settings['vr_settings']['queue_refresh_time_microsec']
        )
    )

    # create workers -----------------------------------------------------------------------
    camera_worker = CameraWorker(
        camera_constructor = settings['camera']['camera_constructor'], 
        exposure = settings['camera']['exposure_value'],
        gain = settings['camera']['gain_value'],
        framerate = settings['camera']['framerate_value'],
        height = settings['camera']['height_value'],
        width = settings['camera']['width_value'],
        offsetx = settings['camera']['offsetX_value'],
        offsety = settings['camera']['offsetY_value'],
        name = 'camera', 
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_strategy = receive_strategy.COLLECT, 
        send_data_strategy = send_strategy.BROADCAST, 
        receive_data_timeout = 1.0,
    )

    queue_monitor_worker = QueueMonitor(
        queues = {
            queue_cam: 'camera to background',
            queue_background: 'background to trackers',
            queue_tracking: 'tracking to stim',
            queue_overlay: 'tracking to overlay',
        },
        name = 'queue_monitor',
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0,
    )

    # background subtraction ------------------------------------
    if settings['background']['bckgsub_polarity'] == 'dark on bright':
        background_polarity = Polarity.DARK_ON_BRIGHT  
    else:
        background_polarity = Polarity.BRIGHT_ON_DARK

    background = BackroundImage(
        image_file_name = settings['background']['background_file'],
        polarity = background_polarity,
        use_gpu = settings['vr_settings']['background_gpu']
    )

    background_worker_list = []
    for i in range(settings['vr_settings']['n_background_workers']):
        background_worker_list.append(
            BackgroundSubWorker(
                background, 
                name = f'background{i}', 
                logger = worker_logger, 
                logger_queues = queue_logger,
                receive_data_timeout = 1.0, 
                    )
        )

    # tracking --------------------------------------------------
    assignment = np.zeros(
        (settings['camera']['height_value'], settings['camera']['width_value']), 
        dtype=np.int_
    )
    tracker = MultiFishTracker_CPU(
        MultiFishTrackerParamTracking(
            accumulator = None,
            animal = AnimalTracker_CPU(
                assignment = GridAssignment(LUT = assignment), 
                tracking_param = AnimalTrackerParamTracking(
                    source_image_shape = (settings['camera']['height_value'], settings['camera']['width_value'])
                )
            ),
            body = BodyTracker_CPU(BodyTrackerParamTracking()), 
            eyes = EyesTracker_CPU(EyesTrackerParamTracking()), 
            tail = TailTracker_CPU(TailTrackerParamTracking())
        )
    )

    tracker_worker_list = []
    for i in range(settings['vr_settings']['n_tracker_workers']):
        tracker_worker_list.append(
            TrackerWorker(
                tracker, 
                cam_width = settings['camera']['width_value'],
                cam_height = settings['camera']['height_value'],
                n_tracker_workers = settings['vr_settings']['n_tracker_workers'],
                name = f'tracker{i}', 
                logger = worker_logger, 
                logger_queues = queue_logger,
                send_data_strategy = send_strategy.BROADCAST, 
                receive_data_timeout = 1.0, 
                        )
        )
    
    tracker_control_worker = TrackerGui(
        n_tracker_workers = settings['vr_settings']['n_tracker_workers'],
        settings_file = settings['vr_settings']['tracking_file'],
        name = 'tracker_gui',  
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0, # TODO add widget for that ?
        profile = False
    )

    # tracking display -----------------------------------------
    overlay = MultiFishOverlay_opencv(
        MultiFishTrackerParamOverlay(
            AnimalOverlay_opencv(AnimalTrackerParamOverlay()),
            BodyOverlay_opencv(BodyTrackerParamOverlay()),
            EyesOverlay_opencv(EyesTrackerParamOverlay()),
            TailOverlay_opencv(TailTrackerParamOverlay())
        )
    )

    tracking_display_worker = TrackingDisplay(
        overlay = overlay, 
        fps = settings['vr_settings']['display_fps'], 
        name = "tracking_display", 
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0,
        profile = False
    )

    tracking_saver_worker = TrackingSaver(
        filename = settings['output']['csv_filename'],
        num_tail_points_interp = settings['vr_settings']['n_tail_pts_interp'],
        name = 'tracking_saver',
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0,
    )

    # connect DAG -----------------------------------------------------------------------
    # data
    for i in range(settings['vr_settings']['n_background_workers']):   
        dag.connect_data(
            sender = camera_worker, 
            receiver = background_worker_list[i], 
            queue = queue_cam, 
            name = 'cam_output1'
        )

    for i in range(settings['vr_settings']['n_background_workers']):
        for j in range(settings['vr_settings']['n_tracker_workers']):
            dag.connect_data(
                sender = background_worker_list[i], 
                receiver = tracker_worker_list[j], 
                queue = queue_background, 
                name = 'background_subtracted'
            )


    for i in range(settings['vr_settings']['n_tracker_workers']):
        dag.connect_data(
            sender = tracker_worker_list[i], 
            receiver = tracking_display_worker, 
            queue = queue_overlay, 
            name = 'tracker_output2'
        )

    for i in range(settings['vr_settings']['n_tracker_workers']):
        dag.connect_data(
            sender = tracker_worker_list[i], 
            receiver = tracking_saver_worker, 
            queue = queue_tracking, 
            name = 'tracker_output1'
        )

    # metadata
    for i in range(settings['vr_settings']['n_tracker_workers']):
        dag.connect_metadata(
            sender = tracker_control_worker, 
            receiver = tracker_worker_list[i], 
            queue = QueueMP(), 
            name = f'tracker_control_{i}'
        )

    # isolated nodes
    dag.add_node(queue_monitor_worker)

    return (dag, worker_logger, queue_logger)