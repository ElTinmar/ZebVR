from typing import Dict, Optional, Tuple
import numpy as np

from multiprocessing_logger import Logger
from ipc_tools import MonitoredQueue, ModifiableRingBuffer, QueueMP
from dagline import ProcessingDAG, receive_strategy, send_strategy
from geometry import AffineTransform2D
from tracker import SingleFishOverlay_opencv
from ..workers import (
    CropWorker, 
    AudioStimWorker,
    CameraWorker, 
    TrackerWorker, 
    ImageSaverWorker, 
    VideoSaverWorker,
    TrackerGui, 
    StimGUI,
    TrackingDisplay,
    Display,
    Protocol,
    QueueMonitor,
    ImageFilterWorker, 
    TrackingSaver,
    TemperatureLoggerWorker,
    DAQ_Worker,
    LatencyDisplay,
    StimSaver,
    rgb_to_yuv420p,
    rgb_to_gray
)
from ..stimulus import VisualStimWorker, GeneralStim
from ..utils import tracker_from_json

DEFAULT_QUEUE_SIZE_MB = 500
PROFILE = False

def closed_loop(settings: Dict, dag: Optional[ProcessingDAG] = None) -> Tuple[ProcessingDAG, Logger, Logger]:
    
    # create DAG
    if dag is None:
        dag = ProcessingDAG()
    
    # create loggers
    worker_logger = Logger(settings['logs']['log']['worker_logfile'], Logger.INFO)
    queue_logger = Logger(settings['logs']['log']['queue_logfile'], Logger.INFO)

    # create queues -----------------------------------------------------------------------            
    queue_camera_to_converter = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = DEFAULT_QUEUE_SIZE_MB*1024**2,
            logger = queue_logger,
            name = 'camera_to_converter',
                    )
    )

    queue_converter_to_saver = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = DEFAULT_QUEUE_SIZE_MB*1024**2,
            logger = queue_logger,
            name = 'converter_to_saver',
                    )
    )

    queue_save_image = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = DEFAULT_QUEUE_SIZE_MB*1024**2,
            logger = queue_logger,
            name = 'camera_to_image_saver',
                    )
    )

    queue_display_image = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = DEFAULT_QUEUE_SIZE_MB*1024**2,
            logger = queue_logger,
            name = 'image_saver_to_display',
                    )
    )

    queue_cam_to_cropper = MonitoredQueue(ModifiableRingBuffer(
        num_bytes = DEFAULT_QUEUE_SIZE_MB*1024**2,
        #copy=False, # you probably don't need to copy if processing is fast enough
        logger = queue_logger,
        name = 'camera_to_crop',
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
                num_bytes = 200*1024**2,
                logger = queue_logger,
                name = 'tracker_to_stim',
                            ))
        )

        queue_tracking_to_overlay.append(
            MonitoredQueue(ModifiableRingBuffer(
                num_bytes = 200*1024**2,
                logger = queue_logger,
                name = 'tracker_to_overlay',
                            ))
        )

        queue_tracking_to_saver.append(
            MonitoredQueue(ModifiableRingBuffer(
                num_bytes = 200*1024**2,
                logger = queue_logger,
                name = 'tracker_to_overlay',
                            ))
        )

    queue_trigger_metadata = MonitoredQueue(
        ModifiableRingBuffer(
            num_bytes = 200*1024**2,
            logger = queue_logger,
            name = 'tracker_to_protocol',
                    )
    )

    queue_stim_saver = QueueMP()

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
        log_level = Logger.ERROR,
        receive_data_strategy = receive_strategy.COLLECT, 
        send_data_strategy = send_strategy.BROADCAST, 
        receive_data_timeout = 1.0,
        profile = PROFILE
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
        log_level = Logger.ERROR,
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
        log_level = Logger.ERROR,
        receive_data_timeout = 1.0,
    )

    yuv420p_converter = ImageFilterWorker(
        image_function=rgb_to_yuv420p,
        name = 'yuv420p_converter',
        logger = worker_logger, 
        logger_queues = queue_logger,
        log_level = Logger.ERROR,
        receive_data_timeout = 1.0,
    )

    rgb_to_gray_converter = ImageFilterWorker(
        image_function=rgb_to_gray,
        name = 'rgb_to_gray_converter',
        logger = worker_logger, 
        logger_queues = queue_logger,
        log_level = Logger.ERROR,
        receive_data_timeout = 1.0,
    )

    queues = {
        queue_cam_to_cropper: 'camera to crop',
        queue_display_image: 'display',
        queue_save_image: 'direct video recording',
        queue_camera_to_converter: 'pixel format conversion',
        queue_converter_to_saver: 'converted video recording',
        queue_trigger_metadata: 'tracker to protocol',
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
        log_level = Logger.ERROR,
        receive_data_timeout = 1.0,
    )

    temperature_logger = TemperatureLoggerWorker(
        filename = settings['temperature']['csv_filename'],
        serial_port = settings['temperature']['serial_port'],
        name = 'temperature_logger',
        logger = worker_logger, 
        logger_queues = queue_logger,
        log_level = Logger.ERROR,
    )

    daq_worker = DAQ_Worker(
        daq_boards = settings['daq'],
        name = 'daq',
        logger = worker_logger, 
        logger_queues = queue_logger,
        log_level = Logger.ERROR,
        send_metadata_strategy = send_strategy.DISPATCH
    )

    cropper = CropWorker(
        ROI_identities = settings['identity']['ROIs'],
        name = f'crop', 
        logger = worker_logger, 
        logger_queues = queue_logger,
        log_level = Logger.ERROR,
        receive_data_timeout = 1.0, 
        send_data_strategy = send_strategy.BROADCAST,
        profile = PROFILE
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
                log_level = Logger.ERROR,
                send_data_strategy = send_strategy.BROADCAST, 
                #receive_metadata_strategy = receive_strategy.POLL,
                receive_data_timeout = 1.0, 
                profile = PROFILE
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
        log_level = Logger.ERROR,
        receive_data_timeout = 1.0, # TODO add widget for that ?
        profile = False
    )

    tracking_saver_worker = TrackingSaver(
        filename = settings['settings']['tracking']['csv_filename'],
        num_tail_points_interp = settings['settings']['tracking']['n_tail_pts_interp'],
        name = 'tracking_saver',
        logger = worker_logger, 
        logger_queues = queue_logger,
        log_level = Logger.ERROR,
        receive_data_timeout = 1.0,
    )

    tracking_latency_display = LatencyDisplay(
        name = 'tracking_latency_display',
        logger = worker_logger, 
        logger_queues = queue_logger,
        log_level = Logger.ERROR,
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
        log_level = Logger.ERROR,
        receive_data_timeout = 1.0,
        profile = False
    )

    display_worker = Display(
        fps = settings['settings']['videorecording']['display_fps'], 
        name = "display", 
        logger = worker_logger, 
        logger_queues = queue_logger,
        log_level = Logger.ERROR,
        receive_data_timeout = 1.0,
        profile = False
    )

    # protocol -------------------------------------------------
    protocol_worker = Protocol(
        name = "protocol", 
        logger = worker_logger, 
        logger_queues = queue_logger,
        log_level = Logger.ERROR,
        receive_data_timeout = 1.0,
        profile = False
    )

    # visual stim ----------------------------------------------
    stim = GeneralStim(
        ROI_identities = settings['identity']['ROIs'],
        window_size = settings['projector']['resolution'],
        window_position = settings['projector']['offset'],
        window_decoration = False,
        camera_resolution = (settings['camera']['width_value'], settings['camera']['height_value']),
        transformation_matrix = AffineTransform2D.from_array(np.array(settings['registration']['transformation_matrix'])),
        pixel_scaling = settings['projector']['pixel_scale'],
        pix_per_mm = settings['calibration']['pix_per_mm'],
        refresh_rate = settings['projector']['fps'],
        vsync = True,
        fullscreen = settings['projector']['fullscreen'],
        num_tail_points_interp = settings['settings']['tracking']['n_tail_pts_interp']
    )

    stim_worker = VisualStimWorker(
        stim = stim, 
        name = 'visual_stim', 
        logger = worker_logger, 
        logger_queues = queue_logger,
        log_level = Logger.ERROR,
        receive_data_timeout = 1.0,
        profile = False,
        send_metadata_strategy = send_strategy.DISPATCH
    )

    audio_stim_worker = AudioStimWorker(
        units_per_dB = settings['audio']['units_per_dB'],
        device_index = settings['audio']['device_index'],
        samplerate = settings['audio']['samplerate'], 
        blocksize = settings['audio']['blocksize'], 
        channels = settings['audio']['channels'],
        rollover_time_sec = settings['audio']['rollover_time_sec'],
        name = 'audio_stim', 
        logger = worker_logger, 
        logger_queues = queue_logger,
        log_level = Logger.ERROR,
        receive_data_timeout = 1.0,
        send_metadata_strategy = send_strategy.DISPATCH
    )

    stim_control_worker = StimGUI(
        daq_boards = settings['daq'],
        name = 'stim_gui', 
        logger = worker_logger, 
        logger_queues = queue_logger,
        log_level = Logger.ERROR,
        receive_data_timeout = 1.0,
        send_metadata_strategy = send_strategy.BROADCAST, 
        profile = False
    ) 

    stim_saver = StimSaver(
        filename = settings['settings']['stim_output']['filename'],
        name = 'stim_saver', 
        logger = worker_logger, 
        logger_queues = queue_logger,
        log_level = Logger.ERROR,
        receive_data_timeout = 1.0,
        receive_metadata_strategy = receive_strategy.POLL
    )

    # connect DAG -----------------------------------------------------------------------
    # data
    dag.connect_data(
        sender = camera_worker, 
        receiver = cropper, 
        queue = queue_cam_to_cropper, 
        name = 'cam_output1'
    )

    if settings['settings']['videorecording']['video_recording']:

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

    for i in range(settings['identity']['n_animals']):
        dag.connect_data(
            sender = cropper, 
            receiver = tracker_worker_list[i], 
            queue = queue_crop_to_tracker[i], 
            name = f'cropper_output_{i}'
        )

        dag.connect_data(
            sender = tracker_worker_list[i], 
            receiver = stim_worker, 
            queue = queue_tracking_to_stim[i], 
            name = f'tracker_output_stim'
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

    dag.connect_data(
        sender = tracking_saver_worker, 
        receiver = tracking_latency_display, 
        queue = QueueMP(), 
        name = 'tracking_latency'
    )

    # metadata
    if settings['main']['record']:
        protocol = settings['sequencer']['protocol']
        protocol_worker.set_protocol(protocol)
        dag.connect_metadata(
            sender = protocol_worker, 
            receiver = stim_worker, 
            queue = QueueMP(), 
            name = 'stim_control'
        )
        if settings['audio']['enabled']:
            dag.connect_metadata(
                sender = protocol_worker, 
                receiver = audio_stim_worker, 
                queue = QueueMP(), 
                name = 'audio_stim_control'
            )
        dag.connect_metadata(
            sender = protocol_worker, 
            receiver = daq_worker, 
            queue = QueueMP(), 
            name = 'daq_stim_control'
        )
        for i in range(settings['identity']['n_animals']):
            dag.connect_metadata(
                sender = tracker_worker_list[i], 
                receiver = protocol_worker, 
                queue = queue_trigger_metadata, 
                name = 'tracker_metadata'
            )
    else:
        dag.connect_metadata(
            sender = stim_control_worker, 
            receiver= stim_worker, 
            queue = QueueMP(), 
            name = 'stim_control'
        )
        if settings['audio']['enabled']:
            dag.connect_metadata(
                sender = stim_control_worker, 
                receiver = audio_stim_worker, 
                queue = QueueMP(), 
                name = 'audio_stim_control'
            )
        dag.connect_metadata(
            sender = stim_control_worker, 
            receiver = daq_worker, 
            queue = QueueMP(), 
            name = 'daq_stim_control'
        )
        
    for i in range(settings['identity']['n_animals']):
        dag.connect_metadata(
            sender = tracker_control_worker, 
            receiver = tracker_worker_list[i], 
            queue = QueueMP(), # multiple queues
            name = f'tracker_control_{i}'
        )

    dag.connect_metadata(
        sender = stim_worker,
        receiver = stim_saver,
        queue = queue_stim_saver, 
        name = 'visual_stim_logger'
    )
    dag.connect_metadata(
        sender = daq_worker,
        receiver = stim_saver,
        queue = queue_stim_saver, 
        name = 'daq_stim_logger'
    )
    if settings['audio']['enabled']:
        dag.connect_metadata(
            sender = audio_stim_worker,
            receiver = stim_saver,
            queue = queue_stim_saver, 
            name = 'audio_stim_logger'
        )

    # isolated nodes
    dag.add_node(queue_monitor_worker)

    if settings['temperature']['serial_port'] != '':
        dag.add_node(temperature_logger)

    return (dag, worker_logger, queue_logger)