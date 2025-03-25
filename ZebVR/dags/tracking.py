from typing import Dict, Optional, Tuple
import numpy as np
import json

from multiprocessing_logger import Logger
from ipc_tools import MonitoredQueue, ModifiableRingBuffer, QueueMP
from video_tools import BackgroundImage, Polarity
from dagline import ProcessingDAG, receive_strategy, send_strategy
from tracker import (
    GridAssignment, 
    LinearSumAssignment,
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
from ..workers import (
    BackgroundSubWorker, 
    CameraWorker, 
    TrackerWorker, 
    CropWorker,
    TrackerGui, 
    TrackingDisplay,
    QueueMonitor,
    TrackingSaver
)

DEFAULT_QUEUE_SIZE_MB = 100

def tracking(settings: Dict, dag: Optional[ProcessingDAG] = None) -> Tuple[ProcessingDAG, Logger, Logger]:
    
    # create DAG
    if dag is None:
        dag = ProcessingDAG()
    
    # create loggers
    worker_logger = Logger(settings['logs']['log']['worker_logfile'], Logger.INFO)
    queue_logger = Logger(settings['logs']['log']['queue_logfile'], Logger.INFO)

    # create queues -----------------------------------------------------------------------            
    queue_cam_to_background = MonitoredQueue(ModifiableRingBuffer(
        num_bytes = DEFAULT_QUEUE_SIZE_MB*1024**2,
        #copy=False, # you probably don't need to copy if processing is fast enough
        logger = queue_logger,
        name = 'background_to_crop',
        t_refresh = 1e-6 * settings['logs']['queue_refresh_time_microsec']
    ))

    queue_background_to_cropper = MonitoredQueue(ModifiableRingBuffer(
        num_bytes = DEFAULT_QUEUE_SIZE_MB*1024**2,
        #copy=False, # you probably don't need to copy if processing is fast enough
        logger = queue_logger,
        name = 'background_to_crop',
        t_refresh = 1e-6 * settings['logs']['queue_refresh_time_microsec']
    ))

    queue_crop_to_tracker = []
    queue_tracking_to_stim = []
    queue_tracking_to_overlay = []
    queue_tracking_to_saver = []

    for i in range(settings['identity']['n_animals']):

        queue_crop_to_tracker.append(
            MonitoredQueue(ModifiableRingBuffer(
                num_bytes = DEFAULT_QUEUE_SIZE_MB*1024**2,
                #copy=False, # you probably don't need to copy if processing is fast enough
                logger = queue_logger,
                name = 'background_to_trackers',
                t_refresh = 1e-6 * settings['logs']['queue_refresh_time_microsec']
            ))
        )
        
        queue_tracking_to_stim.append(
            MonitoredQueue(ModifiableRingBuffer(
                num_bytes = DEFAULT_QUEUE_SIZE_MB*1024**2,
                logger = queue_logger,
                name = 'tracker_to_stim',
                t_refresh = 1e-6 * settings['logs']['queue_refresh_time_microsec']
            ))
        )

        queue_tracking_to_overlay.append(
            MonitoredQueue(ModifiableRingBuffer(
                num_bytes = DEFAULT_QUEUE_SIZE_MB*1024**2,
                logger = queue_logger,
                name = 'tracker_to_overlay',
                t_refresh = 1e-6 * settings['logs']['queue_refresh_time_microsec']
            ))
        )

        queue_tracking_to_saver.append(
            MonitoredQueue(ModifiableRingBuffer(
                num_bytes = DEFAULT_QUEUE_SIZE_MB*1024**2,
                logger = queue_logger,
                name = 'tracker_to_overlay',
                t_refresh = 1e-6 * settings['logs']['queue_refresh_time_microsec']
            ))
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

    queues = {
        queue_cam_to_background: 'camera to background',
        queue_background_to_cropper: 'backgroud_to_cropper',
    }
    queues.update({q: f'tracking to stim {n}' for n,q in enumerate(queue_tracking_to_stim)})
    queues.update({q: f'crop to tracker {n}' for n,q in enumerate(queue_crop_to_tracker)})
    queues.update({q: f'tracking to overlay {n}' for n,q in enumerate(queue_tracking_to_overlay)})
    queues.update({q: f'tracking to saver {n}' for n,q in enumerate(queue_tracking_to_saver)})

    queue_monitor_worker = QueueMonitor(
        queues = queues,
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

    background = BackgroundImage(
        image_file_name = settings['background']['background_file'],
        polarity = background_polarity,
        use_gpu = settings['settings']['tracking']['background_gpu']
    )

    background_worker = BackgroundSubWorker(
        background, 
        name = f'background{i}', 
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0, 
    )

    cropper = CropWorker(
        ROI_identities = settings['identity']['ROIs'],
        name = f'crop', 
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0, 
        send_data_strategy = send_strategy.BROADCAST,
    )

    # tracking --------------------------------------------------
    # TODO fix that, add a ROI selection tool
    LUT = np.zeros(
        (settings['camera']['height_value'], settings['camera']['width_value']), 
        dtype=np.int_
    )

    with open(settings['settings']['tracking']['tracker_settings_file'],'r') as fp:
        tracker_settings = json.load(fp)

    if tracker_settings['assignment'] == 'ROI':
        assignment = GridAssignment(
            LUT=LUT, # TODO fix that, add a ROI selection tool
            num_animals = tracker_settings['animal_tracking']['num_animals']
        )
    elif tracker_settings['assignment'] == 'Hungarian':
        assignment = LinearSumAssignment(
            distance_threshold = 20, # TODO fix that, add a widget
            num_animals = tracker_settings['animal_tracking']['num_animals']
        )
    else:
        raise ValueError('incorrect assignment method')

    body = eyes = tail = None
    if tracker_settings['body_tracking_enabled']:
        body = BodyTracker_CPU(BodyTrackerParamTracking(**tracker_settings['body_tracking']))

    if tracker_settings['eyes_tracking_enabled']:
        eyes = EyesTracker_CPU(EyesTrackerParamTracking(**tracker_settings['eyes_tracking']))

    if tracker_settings['tail_tracking_enabled']:
        tail = TailTracker_CPU(TailTrackerParamTracking(**tracker_settings['tail_tracking']))

    tracker = MultiFishTracker_CPU(
        MultiFishTrackerParamTracking(
            accumulator = None,
            animal = AnimalTracker_CPU(
                assignment = assignment, 
                tracking_param = AnimalTrackerParamTracking(**tracker_settings['animal_tracking'])
            ),
            body = body, 
            eyes = eyes, 
            tail = tail
        )
    )

    tracker_worker_list = []
    for i in range(settings['identity']['n_animals']):
        tracker_worker_list.append(
            TrackerWorker(
                tracker, 
                cam_width = settings['camera']['width_value'],
                cam_height = settings['camera']['height_value'],
                n_tracker_workers = settings['identity']['n_animals'],
                name = f'tracker{i}', 
                logger = worker_logger, 
                logger_queues = queue_logger,
                send_data_strategy = send_strategy.BROADCAST, 
                receive_data_timeout = 1.0, 
            )
        )
    
    tracker_control_worker = TrackerGui(
        n_tracker_workers = settings['identity']['n_animals'],
        settings_file = settings['settings']['tracking']['tracker_settings_file'],
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
        fps = settings['settings']['tracking']['display_fps'], 
        n_animals = settings['identity']['n_animals'],
        name = "tracking_display", 
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0,
        profile = False
    )

    tracking_saver_worker = TrackingSaver(
        filename = settings['settings']['tracking']['csv_filename'],
        num_tail_points_interp = settings['settings']['tracking']['n_tail_pts_interp'],
        name = 'tracking_saver',
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0,
    )

    # connect DAG -----------------------------------------------------------------------
    # data
    dag.connect_data(
        sender = camera_worker, 
        receiver = background_worker, 
        queue = queue_cam_to_background, 
        name = 'cam_output1'
    )

    dag.connect_data(
        sender = background_worker, 
        receiver = cropper, 
        queue = queue_background_to_cropper, 
        name = 'background_to_crop'
    )

    for i in range(settings['identity']['n_animals']):
        dag.connect_data(
            sender = cropper, 
            receiver = tracker_worker_list[i], 
            queue = queue_crop_to_tracker[i], 
            name = f'background_output_{i}'
        )

        dag.connect_data(
            sender = tracker_worker_list[i], 
            receiver = tracking_display_worker, 
            queue = queue_tracking_to_overlay[i], 
            name = 'tracker_output_overlay'
        )

        dag.connect_data(
            sender = tracker_worker_list[i], 
            receiver = tracking_saver_worker, 
            queue = queue_tracking_to_saver[i], 
            name = 'tracker_output_saver'
        )

    # metadata
    for i in range(settings['identity']['n_animals']):
        dag.connect_metadata(
            sender = tracker_control_worker, 
            receiver = tracker_worker_list[i], 
            queue = QueueMP(), 
            name = f'tracker_control_{i}'
        )

    # isolated nodes
    dag.add_node(queue_monitor_worker)

    return (dag, worker_logger, queue_logger)