from typing import Dict, Optional
import numpy as np

from multiprocessing_logger import Logger
from ipc_tools import MonitoredQueue, ModifiableRingBuffer, QueueMP
from video_tools import BackroundImage, Polarity
from dagline import ProcessingDAG, receive_strategy, send_strategy
from tracker import (
    GridAssignment, 
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
from ZebVR.workers import (
    BackgroundSubWorker, 
    CameraWorker, 
    TrackerWorker, 
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
from ZebVR.stimulus import VisualStimWorker, GeneralStim

def open_loop(settings: Dict, dag: Optional[ProcessingDAG]) -> ProcessingDAG:
    
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

    queue_camera_to_converter = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            logger = queue_logger,
            name = 'camera_to_converter',
            t_refresh = 1e-6 * settings['vr_settings']['queue_refresh_time_microsec']
        )
    )

    queue_converter_to_saver = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            logger = queue_logger,
            name = 'converter_to_saver',
            t_refresh = 1e-6 * settings['vr_settings']['queue_refresh_time_microsec']
        )
    )

    queue_save_image = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            logger = queue_logger,
            name = 'camera_to_image_saver',
            t_refresh = 1e-6 * settings['vr_settings']['queue_refresh_time_microsec']
        )
    )

    queue_display_image = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            logger = queue_logger,
            name = 'image_saver_to_display',
            t_refresh = 1e-6 * settings['vr_settings']['queue_refresh_time_microsec']
        )
    )

    queue_background = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            #copy=False, # you probably don't need to copy if processing is fast enough
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

    # video recording ------------------------------------------
    image_saver_worker = ImageSaverWorker(
        folder = settings['output']['video_recording_dir'], 
        decimation = settings['output']['video_decimation'],
        compress = settings['output']['video_recording_compression'],
        resize = settings['output']['video_recording_resize'],
        name = 'cam_output2',  
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0,
    )

    video_recorder_worker = VideoSaverWorker(
        height = settings['camera']['height_value'],
        width = settings['camera']['width_value'],
        filename = settings['output']['video_filename'],
        decimation = settings['output']['video_decimation'],
        fps = settings['camera']['framerate_value']/settings['output']['video_decimation'],
        video_codec = settings['output']['video_codec'],
        gpu = settings['output']['video_gpu'],
        grayscale = settings['output']['video_grayscale'],
        video_profile = 'main' if not settings['output']['video_grayscale'] else 'high',
        video_preset = settings['output']['video_preset'],
        video_quality = settings['output']['video_quality'],
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
            queue_cam: 'camera to background',
            queue_display_image: 'display',
            queue_background: 'background to trackers',
            queue_tracking: 'tracking to stim',
            queue_overlay: 'tracking to overlay',
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
            DummyTrackerWorker(
                tracker,
                centroid = np.array([
                    settings['vr_settings']['centroid_x'],
                    settings['vr_settings']['centroid_y']
                ]),
                heading = np.array(settings['vr_settings']['heading']), # TODO check transposition is warranted (PC on col vs rows)
                name = f'tracker{i}', 
                logger = worker_logger, 
                logger_queues = queue_logger,
                send_data_strategy = send_strategy.BROADCAST, 
                receive_data_timeout = 1.0, 
                        )
        )

    display_worker = Display(
        fps = settings['vr_settings']['display_fps'], 
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
        transformation_matrix = np.array(settings['registration']['transformation_matrix'], dtype=np.float32),
        pixel_scaling = settings['projector']['pixel_scale'],
        pix_per_mm = settings['calibration']['pix_per_mm'],
        refresh_rate = settings['projector']['fps'],
        vsync = True,
        timings_file = settings['output']['csv_filename'],
        stim_select = 0,
        num_tail_points_interp = settings['vr_settings']['n_tail_pts_interp']
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

    for i in range(settings['vr_settings']['n_tracker_workers']):
        dag.connect_data(
            sender = tracker_worker_list[i], 
            receiver = stim_worker, 
            queue = queue_tracking, 
            name = 'tracker_output1'
        )

    if settings['output']['video_recording']:

        if settings['output']['video_method'] == 'image sequence':
            dag.connect_data(
                sender = camera_worker, 
                receiver = image_saver_worker, 
                queue = queue_save_image, 
                name = 'cam_output2'
            )
        
        else:
            if settings['camera']['num_channels'] == 3:

                if settings['output']['video_grayscale']:
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

        protocol = settings['protocol']
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

    return dag