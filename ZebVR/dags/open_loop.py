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
    MultiFishTrackerParamTracking,
    AnimalTracker_CPU, 
    AnimalTrackerParamTracking, 
    BodyTracker_CPU,
    BodyTrackerParamTracking,
    EyesTracker_CPU,  
    EyesTrackerParamTracking,
    TailTracker_CPU,
    TailTrackerParamTracking
)
from ..workers import (
    BackgroundSubWorker, 
    CameraWorker, 
    DummyTrackerWorker,
    ImageSaverWorker, 
    VideoSaverWorker,
    StimGUI,
    Display,
    Protocol,
    QueueMonitor,
    ImageFilterWorker, 
    rgb_to_yuv420p,
    rgb_to_gray
)
from ..stimulus import VisualStimWorker, GeneralStim

def open_loop(settings: Dict, dag: Optional[ProcessingDAG] = None) -> Tuple[ProcessingDAG, Logger, Logger]:
    
    # create DAG
    if dag is None:
        dag = ProcessingDAG()
    
    # create loggers
    worker_logger = Logger(settings['logs']['log']['worker_logfile'], Logger.INFO)
    queue_logger = Logger(settings['logs']['log']['queue_logfile'], Logger.INFO)

    # create queues -----------------------------------------------------------------------            
    queue_cam = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2, # TODO add a widget for that?
            logger = queue_logger,
            name = 'camera_to_tracker',
            t_refresh = 1e-6 * settings['logs']['queue_refresh_time_microsec']
        )
    )

    queue_camera_to_converter = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            logger = queue_logger,
            name = 'camera_to_converter',
            t_refresh = 1e-6 * settings['logs']['queue_refresh_time_microsec']
        )
    )

    queue_converter_to_saver = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            logger = queue_logger,
            name = 'converter_to_saver',
            t_refresh = 1e-6 * settings['logs']['queue_refresh_time_microsec']
        )
    )

    queue_save_image = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            logger = queue_logger,
            name = 'camera_to_image_saver',
            t_refresh = 1e-6 * settings['logs']['queue_refresh_time_microsec']
        )
    )

    queue_display_image = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            logger = queue_logger,
            name = 'image_saver_to_display',
            t_refresh = 1e-6 * settings['logs']['queue_refresh_time_microsec']
        )
    )

    queue_tracking = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            logger = queue_logger,
            name = 'tracker_to_stim',
            t_refresh = 1e-6 * settings['logs']['queue_refresh_time_microsec']
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

    # video recording ------------------------------------------
    image_saver_worker = ImageSaverWorker(
        folder = settings['settings']['videorecording']['video_recording_dir'], 
        decimation = settings['settings']['videorecording']['video_decimation'],
        compress = settings['settings']['videorecording']['video_recording_compression'],
        resize = settings['settings']['videorecording']['video_recording_resize'],
        name = 'cam_output2',  
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0,
    )

    video_recorder_worker = VideoSaverWorker(
        height = settings['camera']['height_value'],
        width = settings['camera']['width_value'],
        filename = settings['settings']['videorecording']['video_filename'],
        decimation = settings['settings']['videorecording']['video_decimation'],
        fps = settings['camera']['framerate_value']/settings['settings']['videorecording']['video_decimation'],
        video_codec = settings['settings']['videorecording']['video_codec'],
        gpu = settings['settings']['videorecording']['video_gpu'],
        grayscale = settings['settings']['videorecording']['video_grayscale'],
        video_profile = 'main' if not settings['settings']['videorecording']['video_grayscale'] else 'high',
        video_preset = settings['settings']['videorecording']['video_preset'],
        video_quality = settings['settings']['videorecording']['video_quality'],
        name = 'video_recorder',
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0,
    )

    yuv420p_converter = ImageFilterWorker(
        image_function=rgb_to_yuv420p,
        name = 'yuv420p_converter',
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0,
    )

    rgb_to_gray_converter = ImageFilterWorker(
        image_function=rgb_to_gray,
        name = 'rgb_to_gray_converter',
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0,
    )

    queue_monitor_worker = QueueMonitor(
        queues = {
            queue_cam: 'camera to tarcker',
            queue_display_image: 'display',
            queue_tracking: 'tracking to stim',
            queue_save_image: 'direct video recording',
            queue_camera_to_converter: 'pixel format conversion',
            queue_converter_to_saver: 'converted video recording',
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

    background = BackgroundImage(
        image_file_name = settings['background']['background_file'],
        polarity = background_polarity,
        use_gpu = settings['settings']['tracking']['background_gpu']
    )

    background_worker_list = []
    for i in range(settings['settings']['tracking']['n_background_workers']):
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
    for i in range(settings['settings']['tracking']['n_tracker_workers']):
        tracker_worker_list.append(
            DummyTrackerWorker(
                tracker,
                centroid = np.array([
                    settings['settings']['openloop']['centroid_x'],
                    settings['settings']['openloop']['centroid_y']
                ]),
                heading = np.array(settings['settings']['openloop']['heading']), 
                name = f'tracker{i}', 
                logger = worker_logger, 
                logger_queues = queue_logger,
                send_data_strategy = send_strategy.BROADCAST, 
                receive_data_timeout = 1.0, 
            )
        )

    display_worker = Display(
        fps = settings['settings']['videorecording']['display_fps'],
        name = "display", 
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0,
        profile = False
    )

    # protocol -------------------------------------------------
    protocol_worker = Protocol(
        name = "protocol", 
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0,
        profile = False
    )

    # visual stim ----------------------------------------------
    stim = GeneralStim(
        window_size = settings['projector']['resolution'],
        window_position = settings['projector']['offset'],
        window_decoration = False,
        camera_resolution = (settings['camera']['width_value'], settings['camera']['height_value']),
        transformation_matrix = np.array(settings['registration']['transformation_matrix'], dtype=np.float32),
        pixel_scaling = settings['projector']['pixel_scale'],
        pix_per_mm = settings['calibration']['pix_per_mm'],
        refresh_rate = settings['projector']['fps'],
        vsync = True,
        timings_file = settings['settings']['tracking']['csv_filename'],
        stim_select = 0,
        num_tail_points_interp = settings['settings']['tracking']['n_tail_pts_interp']
    )

    stim_worker = VisualStimWorker(
        stim = stim, 
        name = 'visual_stim', 
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0,
        profile = False
    )

    stim_control_worker = StimGUI(
        name = 'stim_gui', 
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0,
        profile = False
    ) 

    # connect DAG -----------------------------------------------------------------------

    for i in range(settings['settings']['tracking']['n_tracker_workers']):
        dag.connect_data(
            sender = tracker_worker_list[i], 
            receiver = stim_worker, 
            queue = queue_tracking, 
            name = 'tracker_output1'
        )

    if settings['settings']['videorecording']['video_recording']:

        for i in range(settings['settings']['tracking']['n_tracker_workers']):
            dag.connect_data(
                sender = camera_worker, 
                receiver = tracker_worker_list[i], 
                queue = queue_cam, 
                name = 'cam_output1'
            )

        if settings['settings']['videorecording']['video_method'] == 'image sequence':
            dag.connect_data(
                sender = camera_worker, 
                receiver = image_saver_worker, 
                queue = queue_save_image, 
                name = 'cam_output2'
            )
        
        else:
            if settings['camera']['num_channels'] == 3:

                if settings['settings']['videorecording']['video_grayscale']:
                    dag.connect_data(
                        sender = camera_worker, 
                        receiver = rgb_to_gray_converter, 
                        queue = queue_camera_to_converter, 
                        name = 'cam_output2'
                    )

                    dag.connect_data(
                        sender = rgb_to_gray_converter, 
                        receiver = video_recorder_worker, 
                        queue = queue_converter_to_saver, 
                        name = 'gray_compression'
                    )

                else:
                    dag.connect_data(
                        sender = camera_worker, 
                        receiver = yuv420p_converter, 
                        queue = queue_camera_to_converter, 
                        name = 'cam_output2'
                    )

                    dag.connect_data(
                        sender = yuv420p_converter, 
                        receiver = video_recorder_worker, 
                        queue = queue_converter_to_saver, 
                        name = 'yuv420p_compression'
                    )

            else:

                dag.connect_data(
                    sender = camera_worker, 
                    receiver = video_recorder_worker, 
                    queue = queue_save_image, 
                    name = 'cam_output2'
                )

        dag.connect_data(
            sender = video_recorder_worker, 
            receiver = display_worker, 
            queue = queue_display_image, 
            name = 'display_recording'
        )

    if settings['main']['record']:

        protocol = settings['sequencer']['protocol']*settings['sequencer']['repetitions']
        protocol_worker.set_protocol(protocol)
        dag.connect_metadata(
            sender = protocol_worker, 
            receiver = stim_worker, 
            queue = QueueMP(), 
            name = 'visual_stim_control'
        )

    else:

        dag.connect_metadata(
            sender = stim_control_worker, 
            receiver = stim_worker, 
            queue = QueueMP(), 
            name = 'visual_stim_control'
        )

    dag.add_node(queue_monitor_worker)

    return (dag, worker_logger, queue_logger)