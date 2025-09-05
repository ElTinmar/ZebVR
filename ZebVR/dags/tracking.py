from typing import Dict, Optional, Tuple

from multiprocessing_logger import Logger
from ipc_tools import MonitoredQueue, ModifiableRingBuffer, QueueMP
from video_tools import BackgroundImage, Polarity
from dagline import ProcessingDAG, receive_strategy, send_strategy
from tracker import (
    SingleFishTracker_CPU,
    SingleFishOverlay_opencv
)
from ..workers import (
    CameraWorker, 
    TrackerWorker, 
    CropWorker,
    TrackerGui, 
    TrackingDisplay,
    QueueMonitor,
    TrackingSaver,
    TemperatureLoggerWorker
)
from ..utils import tracker_from_json

DEFAULT_QUEUE_SIZE_MB = 500

def tracking(settings: Dict, dag: Optional[ProcessingDAG] = None) -> Tuple[ProcessingDAG, Logger, Logger]:
    
    # create DAG
    if dag is None:
        dag = ProcessingDAG()
    
    # create loggers
    worker_logger = Logger(settings['logs']['log']['worker_logfile'], Logger.INFO)
    queue_logger = Logger(settings['logs']['log']['queue_logfile'], Logger.INFO)

    # create queues -----------------------------------------------------------------------            
    queue_cam_to_crop = MonitoredQueue(ModifiableRingBuffer(
        num_bytes = DEFAULT_QUEUE_SIZE_MB*1024**2,
        #copy=False, # you probably don't need to copy if processing is fast enough
        logger = queue_logger,
        name = 'cam_to_crop',
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
                name = 'crop_to_trackers',
            ))
        )
        
        queue_tracking_to_stim.append(
            MonitoredQueue(ModifiableRingBuffer(
                num_bytes = DEFAULT_QUEUE_SIZE_MB*1024**2,
                logger = queue_logger,
                name = 'tracker_to_stim',
                            ))
        )

        queue_tracking_to_overlay.append(
            MonitoredQueue(ModifiableRingBuffer(
                num_bytes = DEFAULT_QUEUE_SIZE_MB*1024**2,
                logger = queue_logger,
                name = 'tracker_to_overlay',
                            ))
        )

        queue_tracking_to_saver.append(
            MonitoredQueue(ModifiableRingBuffer(
                num_bytes = DEFAULT_QUEUE_SIZE_MB*1024**2,
                logger = queue_logger,
                name = 'tracker_to_overlay',
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
        num_channels = settings['camera']['num_channels'],
        name = 'camera', 
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_strategy = receive_strategy.COLLECT, 
        send_data_strategy = send_strategy.BROADCAST, 
        receive_data_timeout = 1.0,
    )

    queues = {
        queue_cam_to_crop: 'camera to cropper',
    }
    queues.update({q: f'crop to tracker {n}' for n,q in enumerate(queue_crop_to_tracker)})
    queues.update({q: f'tracking to stim {n}' for n,q in enumerate(queue_tracking_to_stim)})
    queues.update({q: f'tracking to overlay {n}' for n,q in enumerate(queue_tracking_to_overlay)})
    queues.update({q: f'tracking to saver {n}' for n,q in enumerate(queue_tracking_to_saver)})

    queue_monitor_worker = QueueMonitor(
        queues = queues,
        name = 'queue_monitor',
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
    tracker = tracker_from_json(
        filename = settings['settings']['tracking']['tracker_settings_file'],
        cam_fps = settings['camera']['framerate_value'],
        cam_pix_per_mm = settings['calibration']['pix_per_mm']
    )

    tracker_worker_list = []
    for i in range(settings['identity']['n_animals']):
        tracker_worker_list.append(
            TrackerWorker(
                tracker, 
                background_image_file = settings['background']['background_file'],
                cam_fps = settings['camera']['framerate_value'],
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
        n_animals = settings['identity']['n_animals'],
        settings_file = settings['settings']['tracking']['tracker_settings_file'],
        image_shape = (settings['camera']['height_value'],  settings['camera']['width_value']),
        pix_per_mm = settings['calibration']['pix_per_mm'],
        name = 'tracker_gui',  
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0, # TODO add widget for that ?
        profile = False
    )

    # tracking display -----------------------------------------
    overlay = SingleFishOverlay_opencv()

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
        receiver = cropper, 
        queue = queue_cam_to_crop, 
        name = 'cam_output1'
    )

    for i in range(settings['identity']['n_animals']):
        dag.connect_data(
            sender = cropper, 
            receiver = tracker_worker_list[i], 
            queue = queue_crop_to_tracker[i], 
            name = f'cropper_output_{i}'
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