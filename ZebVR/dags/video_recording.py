from dagline import ProcessingDAG, receive_strategy, send_strategy
from typing import Dict, Tuple, Optional
from ..workers import (
    CameraWorker, 
    ImageSaverWorker, 
    VideoSaverWorker,
    Display,
    QueueMonitor,
    ImageFilterWorker, 
    rgb_to_yuv420p,
    rgb_to_gray
)
from multiprocessing_logger import Logger
from ipc_tools import MonitoredQueue, ModifiableRingBuffer

def video_recording(settings: Dict, dag: Optional[ProcessingDAG] = None) -> Tuple[ProcessingDAG, Logger, Logger]:
    
    # create DAG
    if dag is None:
        dag = ProcessingDAG()
    
    # create loggers
    worker_logger = Logger(settings['settings']['log']['worker_logfile'], Logger.INFO)
    queue_logger = Logger(settings['settings']['log']['queue_logfile'], Logger.INFO)
    
    # create queues -----------------------------------------------------------------------
    queue_cam = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2, 
            logger = queue_logger,
            name = 'camera_to_background',
            t_refresh = 1e-6 * settings['settings']['queue_refresh_time_microsec']
        )
    )

    queue_display_image = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            logger = queue_logger,
            name = 'image_saver_to_display',
            t_refresh = 1e-6 * settings['settings']['queue_refresh_time_microsec']
        )
    )

    queue_camera_to_converter = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            logger = queue_logger,
            name = 'camera_to_converter',
            t_refresh = 1e-6 * settings['settings']['queue_refresh_time_microsec']
        )
    )

    queue_converter_to_saver = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            logger = queue_logger,
            name = 'converter_to_saver',
            t_refresh = 1e-6 * settings['settings']['queue_refresh_time_microsec']
        )
    )

    queue_save_image = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 500*1024**2,
            logger = queue_logger,
            name = 'camera_to_image_saver',
            t_refresh = 1e-6 * settings['settings']['queue_refresh_time_microsec']
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

    display_worker = Display(
        fps = settings['settings']['videorecording']['display_fps'], 
        name = "display", 
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0,
    )

    queue_monitor_worker = QueueMonitor(
        queues = {
            queue_cam: 'camera to background',
            queue_display_image: 'display',
            queue_save_image: 'direct video recording',
            queue_camera_to_converter: 'pixel format conversion',
            queue_converter_to_saver: 'converted video recording',
        },
        name = 'queue_monitor',
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_data_timeout = 1.0,
    )

    # connect DAG -----------------------------------------------------------------------
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

    dag.add_node(queue_monitor_worker)

    return (dag, worker_logger, queue_logger)