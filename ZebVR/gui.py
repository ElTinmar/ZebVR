from multiprocessing import Process
import time
import json

import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QPushButton,
    QTabWidget,
    QMainWindow,
    QAction,
    QFileDialog
)
from PyQt5.QtGui import QIcon

from multiprocessing_logger import Logger
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
from ipc_tools import MonitoredQueue, ModifiableRingBuffer, QueueMP
from video_tools import BackroundImage, Polarity

from ZebVR.calibration import (
    check_pix_per_mm, 
    check_registration, 
    open_loop_coords, 
    pix_per_mm, 
    registration
)
from ZebVR.background import inpaint_background, static_background
from ZebVR.workers import (
    BackgroundSubWorker, 
    CameraWorker, 
    TrackerWorker, 
    DummyTrackerWorker,
    ImageSaverWorker, 
    VideoSaverWorker,
    TrackerGui, 
    StimGUI,
    TrackingDisplay,
    Display,
    Protocol,
    QueueMonitor,
    ImageFilterWorker, 
    rgb_to_yuv420p,
    rgb_to_gray
)
from ZebVR.widgets import (
    CameraWidget, CameraController,
    ProjectorWidget, 
    RegistrationWidget,
    CalibrationWidget,
    BackgroundWidget,
    VRSettingsWidget,
    OutputWidget,
    SequencerWidget
)
from ZebVR.stimulus import VisualStimWorker, GeneralStim

PROFILE = False
        
class MainGui(QMainWindow):
    
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.record_flag = False

        self.settings = {}
        self.dag = None

        self.worker_logger = None
        self.queue_logger = None

        self.camera_worker = None
        self.image_saver_worker = None
        self.background_worker_list = []
        self.tracker_worker_list = []
        self.tracker_control_worker = None
        self.tracking_display_worker = None
        self.protocol_worker = None
        self.stim_worker = None
        self.stim_control_worker = None

        self.create_components()
        self.layout_components()
        self.refresh_settings()
        self.create_loggers()

        self.setWindowTitle('ZebVR')
        self.setWindowIcon(QIcon('ZebVR/resources/zebvr.png'))

    def create_loggers(self):
        
        self.worker_logger = Logger(self.settings['output']['worker_logfile'], Logger.INFO)
        self.queue_logger = Logger(self.settings['output']['queue_logfile'], Logger.INFO)

    def create_workers(self):

        # camera --------------------------------------------------
        self.camera_worker = CameraWorker(
            camera_constructor = self.camera_controller.get_constructor(), 
            exposure = self.settings['camera']['exposure_value'],
            gain = self.settings['camera']['gain_value'],
            framerate = self.settings['camera']['framerate_value'],
            height = self.settings['camera']['height_value'],
            width = self.settings['camera']['width_value'],
            offsetx = self.settings['camera']['offsetX_value'],
            offsety = self.settings['camera']['offsetY_value'],
            name = 'camera', 
            logger = self.worker_logger, 
            logger_queues = self.queue_logger,
            receive_data_strategy = receive_strategy.COLLECT, 
            send_data_strategy = send_strategy.BROADCAST, 
            receive_data_timeout = 1.0,
            profile = PROFILE
        )

        # video recording ------------------------------------------
        self.image_saver_worker = ImageSaverWorker(
            folder = self.settings['output']['video_recording_dir'], 
            decimation = self.settings['output']['video_decimation'],
            compress = self.settings['output']['video_recording_compression'],
            resize = self.settings['output']['video_recording_resize'],
            name = 'cam_output2',  
            logger = self.worker_logger, 
            logger_queues = self.queue_logger,
            receive_data_timeout = 1.0,
            profile = PROFILE
        )

        self.video_recorder_worker = VideoSaverWorker(
            height = self.settings['camera']['height_value'],
            width = self.settings['camera']['width_value'],
            filename = self.settings['output']['video_filename'],
            decimation = self.settings['output']['video_decimation'],
            fps = self.settings['camera']['framerate_value']/self.settings['output']['video_decimation'],
            video_codec = self.settings['output']['video_codec'],
            gpu = self.settings['output']['video_gpu'],
            grayscale = self.settings['output']['video_grayscale'],
            video_profile = 'main' if not self.settings['output']['video_grayscale'] else 'high',
            video_preset = self.settings['output']['video_preset'],
            video_quality = self.settings['output']['video_quality'],
            name = 'video_recorder',
            logger = self.worker_logger, 
            logger_queues = self.queue_logger,
            receive_data_timeout = 1.0,
            profile = PROFILE
        )

        self.yuv420p_converter = ImageFilterWorker(
            image_function=rgb_to_yuv420p,
            name = 'yuv420p_converter',
            logger = self.worker_logger, 
            logger_queues = self.queue_logger,
            receive_data_timeout = 1.0,
            profile = PROFILE 
        )

        self.rgb_to_gray_converter = ImageFilterWorker(
            image_function=rgb_to_gray,
            name = 'rgb_to_gray_converter',
            logger = self.worker_logger, 
            logger_queues = self.queue_logger,
            receive_data_timeout = 1.0,
            profile = PROFILE 
        )

        self.queue_monitor_worker = QueueMonitor(
            queues = {
                self.queue_cam: 'camera to background',
                self.queue_display_image: 'display',
                self.queue_background: 'background to trackers',
                self.queue_tracking: 'tracking to stim',
                self.queue_overlay: 'tracking to overlay',
                self.queue_save_image: 'direct video recording',
                self.queue_camera_to_converter: 'pixel format conversion',
                self.queue_converter_to_saver: 'converted video recording',
            },
            name = 'queue_monitor',
            logger = self.worker_logger, 
            logger_queues = self.queue_logger,
            receive_data_timeout = 1.0,
            profile = PROFILE
        )

        # background subtraction ------------------------------------
        if self.settings['background']['bckgsub_polarity'] == 'dark on bright':
            background_polarity = Polarity.DARK_ON_BRIGHT  
        else:
            background_polarity = Polarity.BRIGHT_ON_DARK

        background = BackroundImage(
            image_file_name = self.settings['background']['background_file'],
            polarity = background_polarity,
            use_gpu = self.settings['vr_settings']['background_gpu']
        )

        self.background_worker_list = []
        for i in range(self.settings['vr_settings']['n_background_workers']):
            self.background_worker_list.append(
                BackgroundSubWorker(
                    background, 
                    name = f'background{i}', 
                    logger = self.worker_logger, 
                    logger_queues = self.queue_logger,
                    receive_data_timeout = 1.0, 
                    profile = PROFILE
                )
            )

        # tracking --------------------------------------------------
        assignment = np.zeros(
            (self.settings['camera']['height_value'], self.settings['camera']['width_value']), 
            dtype=np.int_
        )
        tracker = MultiFishTracker_CPU(
            MultiFishTrackerParamTracking(
                accumulator = None,
                animal = AnimalTracker_CPU(
                    assignment = GridAssignment(LUT = assignment), 
                    tracking_param = AnimalTrackerParamTracking(
                        source_image_shape = (self.settings['camera']['height_value'], self.settings['camera']['width_value'])
                    )
                ),
                body = BodyTracker_CPU(BodyTrackerParamTracking()), 
                eyes = EyesTracker_CPU(EyesTrackerParamTracking()), 
                tail = TailTracker_CPU(TailTrackerParamTracking())
            )
        )

        self.tracker_worker_list = []
        for i in range(self.settings['vr_settings']['n_tracker_workers']):

            if self.settings['vr_settings']['openloop']:
                self.tracker_worker_list.append(
                    DummyTrackerWorker(
                        tracker,
                        centroid = np.array([
                            self.settings['vr_settings']['centroid_x'],
                            self.settings['vr_settings']['centroid_y']
                        ]),
                        heading = np.array(self.settings['vr_settings']['heading']), # TODO check transposition is warranted (PC on col vs rows)
                        name = f'tracker{i}', 
                        logger = self.worker_logger, 
                        logger_queues = self.queue_logger,
                        send_data_strategy = send_strategy.BROADCAST, 
                        receive_data_timeout = 1.0, 
                        profile = PROFILE
                    )
                )

            else:
                self.tracker_worker_list.append(
                    TrackerWorker(
                        tracker, 
                        cam_width = self.settings['camera']['width_value'],
                        cam_height = self.settings['camera']['height_value'],
                        n_tracker_workers = self.settings['vr_settings']['n_tracker_workers'],
                        name = f'tracker{i}', 
                        logger = self.worker_logger, 
                        logger_queues = self.queue_logger,
                        send_data_strategy = send_strategy.BROADCAST, 
                        receive_data_timeout = 1.0, 
                        profile = PROFILE
                    )
                )
        
        self.tracker_control_worker = TrackerGui(
            n_tracker_workers = self.settings['vr_settings']['n_tracker_workers'],
            settings_file = self.settings['vr_settings']['tracking_file'],
            name = 'tracker_gui',  
            logger = self.worker_logger, 
            logger_queues = self.queue_logger,
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

        self.tracking_display_worker = TrackingDisplay(
            overlay = overlay, 
            fps = self.settings['vr_settings']['display_fps'], 
            name = "tracking_display", 
            logger = self.worker_logger, 
            logger_queues = self.queue_logger,
            receive_data_timeout = 1.0,
            profile = False
        )

        self.display_worker = Display(
            fps = self.settings['vr_settings']['display_fps'], 
            name = "display", 
            logger = self.worker_logger, 
            logger_queues = self.queue_logger,
            receive_data_timeout = 1.0,
            profile = False
        )

        # protocol -------------------------------------------------
        self.protocol_worker = Protocol(
            name = "protocol", 
            logger = self.worker_logger, 
            logger_queues = self.queue_logger,
            receive_data_timeout = 1.0,
            profile = False
        )

        # visual stim ----------------------------------------------
        stim = GeneralStim(
            window_size = self.settings['projector']['resolution'],
            window_position = self.settings['projector']['offset'],
            window_decoration = False,
            transformation_matrix = np.array(self.settings['registration']['transformation_matrix'], dtype=np.float32),
            pixel_scaling = self.settings['projector']['pixel_scale'],
            pix_per_mm = self.settings['calibration']['pix_per_mm'],
            refresh_rate = self.settings['projector']['fps'],
            vsync = True,
            timings_file = self.settings['output']['csv_filename'],
            stim_select = 0,
            num_tail_points_interp = self.settings['vr_settings']['n_tail_pts_interp']
        )

        self.stim_worker = VisualStimWorker(
            stim = stim, 
            name = 'visual_stim', 
            logger = self.worker_logger, 
            logger_queues = self.queue_logger,
            receive_data_timeout = 1.0,
            profile = False
        )

        self.stim_control_worker = StimGUI(
            name = 'stim_gui', 
            logger = self.worker_logger, 
            logger_queues = self.queue_logger,
            receive_data_timeout = 1.0,
            profile = False
        ) 

    def create_queues(self):

        # TODO maybe use partial for that
            
        self.queue_cam = MonitoredQueue(
            ModifiableRingBuffer(
                num_bytes = 500*1024**2, # TODO add a widget for that?
                logger = self.queue_logger,
                name = 'camera_to_background',
                t_refresh = 1e-6 * self.settings['vr_settings']['queue_refresh_time_microsec']
            )
        )

        self.queue_camera_to_converter = MonitoredQueue(
            ModifiableRingBuffer(
                num_bytes = 500*1024**2,
                logger = self.queue_logger,
                name = 'camera_to_converter',
                t_refresh = 1e-6 * self.settings['vr_settings']['queue_refresh_time_microsec']
            )
        )

        self.queue_converter_to_saver = MonitoredQueue(
            ModifiableRingBuffer(
                num_bytes = 500*1024**2,
                logger = self.queue_logger,
                name = 'converter_to_saver',
                t_refresh = 1e-6 * self.settings['vr_settings']['queue_refresh_time_microsec']
            )
        )

        self.queue_save_image = MonitoredQueue(
            ModifiableRingBuffer(
                num_bytes = 500*1024**2,
                logger = self.queue_logger,
                name = 'camera_to_image_saver',
                t_refresh = 1e-6 * self.settings['vr_settings']['queue_refresh_time_microsec']
            )
        )

        self.queue_display_image = MonitoredQueue(
            ModifiableRingBuffer(
                num_bytes = 500*1024**2,
                logger = self.queue_logger,
                name = 'image_saver_to_display',
                t_refresh = 1e-6 * self.settings['vr_settings']['queue_refresh_time_microsec']
            )
        )

        self.queue_background = MonitoredQueue(
            ModifiableRingBuffer(
                num_bytes = 500*1024**2,
                #copy=False, # you probably don't need to copy if processing is fast enough
                logger = self.queue_logger,
                name = 'background_to_trackers',
                t_refresh = 1e-6 * self.settings['vr_settings']['queue_refresh_time_microsec']
            )
        )

        self.queue_tracking = MonitoredQueue(
            ModifiableRingBuffer(
                num_bytes = 500*1024**2,
                logger = self.queue_logger,
                name = 'tracker_to_stim',
                t_refresh = 1e-6 * self.settings['vr_settings']['queue_refresh_time_microsec']
            )
        )

        self.queue_overlay = MonitoredQueue(
            ModifiableRingBuffer(
                num_bytes = 500*1024**2,
                logger = self.queue_logger,
                name = 'tracker_to_overlay',
                t_refresh = 1e-6 * self.settings['vr_settings']['queue_refresh_time_microsec']
            )
        )

    def create_video_recording_dag(self):

        # clear workers and queues
        self.create_queues()
        self.create_workers()

        self.dag = ProcessingDAG()

        if self.settings['output']['video_method'] == 'image sequence':
            self.dag.connect_data(
                sender = self.camera_worker, 
                receiver = self.image_saver_worker, 
                queue = self.queue_save_image, 
                name = 'cam_output2'
            )
        
        else:
            if self.settings['camera']['num_channels'] == 3:

                if self.settings['output']['video_grayscale']:
                    self.dag.connect_data(
                        sender = self.camera_worker, 
                        receiver = self.rgb_to_gray_converter, 
                        queue = self.queue_camera_to_converter, 
                        name = 'cam_output2'
                    )

                    self.dag.connect_data(
                        sender = self.rgb_to_gray_converter, 
                        receiver = self.video_recorder_worker, 
                        queue = self.queue_converter_to_saver, 
                        name = 'gray_compression'
                    )

                else:
                    self.dag.connect_data(
                        sender = self.camera_worker, 
                        receiver = self.yuv420p_converter, 
                        queue = self.queue_camera_to_converter, 
                        name = 'cam_output2'
                    )

                    self.dag.connect_data(
                        sender = self.yuv420p_converter, 
                        receiver = self.video_recorder_worker, 
                        queue = self.queue_converter_to_saver, 
                        name = 'yuv420p_compression'
                    )

            else:

                self.dag.connect_data(
                    sender = self.camera_worker, 
                    receiver = self.video_recorder_worker, 
                    queue = self.queue_save_image, 
                    name = 'cam_output2'
                )

        self.dag.connect_data(
            sender = self.video_recorder_worker, 
            receiver = self.display_worker, 
            queue = self.queue_display_image, 
            name = 'display_recording'
        )

        self.dag.add_node(self.queue_monitor_worker)

    def create_open_loop_dag(self):

        # clear workers and queues
        self.create_queues()
        self.create_workers()

        self.dag = ProcessingDAG()

        for i in range(self.settings['vr_settings']['n_tracker_workers']):
            self.dag.connect_data(
                sender = self.tracker_worker_list[i], 
                receiver = self.stim_worker, 
                queue = self.queue_tracking, 
                name = 'tracker_output1'
            )

        if self.settings['output']['video_recording']:

            if self.settings['output']['video_method'] == 'image sequence':
                self.dag.connect_data(
                    sender = self.camera_worker, 
                    receiver = self.image_saver_worker, 
                    queue = self.queue_save_image, 
                    name = 'cam_output2'
                )
            
            else:
                if self.settings['camera']['num_channels'] == 3:

                    if self.settings['output']['video_grayscale']:
                        self.dag.connect_data(
                            sender = self.camera_worker, 
                            receiver = self.rgb_to_gray_converter, 
                            queue = self.queue_camera_to_converter, 
                            name = 'cam_output2'
                        )

                        self.dag.connect_data(
                            sender = self.rgb_to_gray_converter, 
                            receiver = self.video_recorder_worker, 
                            queue = self.queue_converter_to_saver, 
                            name = 'gray_compression'
                        )

                    else:
                        self.dag.connect_data(
                            sender = self.camera_worker, 
                            receiver = self.yuv420p_converter, 
                            queue = self.queue_camera_to_converter, 
                            name = 'cam_output2'
                        )

                        self.dag.connect_data(
                            sender = self.yuv420p_converter, 
                            receiver = self.video_recorder_worker, 
                            queue = self.queue_converter_to_saver, 
                            name = 'yuv420p_compression'
                        )

                else:

                    self.dag.connect_data(
                        sender = self.camera_worker, 
                        receiver = self.video_recorder_worker, 
                        queue = self.queue_save_image, 
                        name = 'cam_output2'
                    )

            self.dag.connect_data(
                sender = self.video_recorder_worker, 
                receiver = self.display_worker, 
                queue = self.queue_display_image, 
                name = 'display_recording'
            )

        if self.record_flag:

            protocol = self.sequencer_widget.get_protocol()
            self.protocol_worker.set_protocol(protocol)
            self.dag.connect_metadata(
                sender = self.protocol_worker, 
                receiver = self.stim_worker, 
                queue = QueueMP(), 
                name = 'visual_stim_control'
            )

        else:

            self.dag.connect_metadata(
                sender = self.stim_control_worker, 
                receiver = self.stim_worker, 
                queue = QueueMP(), 
                name = 'visual_stim_control'
            )

        self.dag.add_node(self.queue_monitor_worker)
            
    def create_closed_loop_dag(self):

        # clear workers and queues
        self.create_queues()
        self.create_workers()

        self.dag = ProcessingDAG()

        # data
        for i in range(self.settings['vr_settings']['n_background_workers']):   
            self.dag.connect_data(
                sender = self.camera_worker, 
                receiver = self.background_worker_list[i], 
                queue = self.queue_cam, 
                name = 'cam_output1'
            )
        
        # NOTE: the order in which you declare connections matter: background_subtraction will
        # be served before image_saver
        if self.settings['output']['video_recording']:

            if self.settings['output']['video_method'] == 'image sequence':
                self.dag.connect_data(
                    sender = self.camera_worker, 
                    receiver = self.image_saver_worker, 
                    queue = self.queue_save_image, 
                    name = 'cam_output2'
                )
            
            else:
                if self.settings['camera']['num_channels'] == 3:

                    if self.settings['output']['video_grayscale']:
                        self.dag.connect_data(
                            sender = self.camera_worker, 
                            receiver = self.rgb_to_gray_converter, 
                            queue = self.queue_camera_to_converter, 
                            name = 'cam_output2'
                        )

                        self.dag.connect_data(
                            sender = self.rgb_to_gray_converter, 
                            receiver = self.video_recorder_worker, 
                            queue = self.queue_converter_to_saver, 
                            name = 'gray_compression'
                        )

                    else:
                        self.dag.connect_data(
                            sender = self.camera_worker, 
                            receiver = self.yuv420p_converter, 
                            queue = self.queue_camera_to_converter, 
                            name = 'cam_output2'
                        )

                        self.dag.connect_data(
                            sender = self.yuv420p_converter, 
                            receiver = self.video_recorder_worker, 
                            queue = self.queue_converter_to_saver, 
                            name = 'yuv420p_compression'
                        )

                else:

                    self.dag.connect_data(
                        sender = self.camera_worker, 
                        receiver = self.video_recorder_worker, 
                        queue = self.queue_save_image, 
                        name = 'cam_output2'
                    )

            self.dag.connect_data(
                sender = self.video_recorder_worker, 
                receiver = self.display_worker, 
                queue = self.queue_display_image, 
                name = 'display_recording'
            )

        for i in range(self.settings['vr_settings']['n_background_workers']):
            for j in range(self.settings['vr_settings']['n_tracker_workers']):
                self.dag.connect_data(
                    sender = self.background_worker_list[i], 
                    receiver = self.tracker_worker_list[j], 
                    queue = self.queue_background, 
                    name = 'background_subtracted'
                )


        for i in range(self.settings['vr_settings']['n_tracker_workers']):
            self.dag.connect_data(
                sender = self.tracker_worker_list[i], 
                receiver = self.tracking_display_worker, 
                queue = self.queue_overlay, 
                name = 'tracker_output2'
            )

        for i in range(self.settings['vr_settings']['n_tracker_workers']):
            self.dag.connect_data(
                sender = self.tracker_worker_list[i], 
                receiver = self.stim_worker, 
                queue = self.queue_tracking, 
                name = 'tracker_output1'
            )

        # metadata

        if self.record_flag:
            protocol = self.sequencer_widget.get_protocol()
            self.protocol_worker.set_protocol(protocol)
            self.dag.connect_metadata(
                sender = self.protocol_worker, 
                receiver = self.stim_worker, 
                queue = QueueMP(), 
                name = 'visual_stim_control'
            )
        else:
            self.dag.connect_metadata(
                sender = self.stim_control_worker, 
                receiver= self.stim_worker, 
                queue = QueueMP(), 
                name = 'visual_stim_control'
            )
            
        for i in range(self.settings['vr_settings']['n_tracker_workers']):
            self.dag.connect_metadata(
                sender = self.tracker_control_worker, 
                receiver = self.tracker_worker_list[i], 
                queue = QueueMP(), 
                name = f'tracker_control_{i}'
            )

        # isolated nodes

        self.dag.add_node(self.queue_monitor_worker)

    def create_components(self):

        self.camera_widget = CameraWidget()
        self.camera_controller = CameraController(self.camera_widget)
        self.camera_controller.state_changed.connect(self.update_camera_settings)

        self.projector_widget = ProjectorWidget()
        self.projector_widget.state_changed.connect(self.update_projector_settings)

        self.registration_widget = RegistrationWidget()
        self.registration_widget.state_changed.connect(self.update_registration_settings)
        self.registration_widget.registration_signal.connect(self.registration_callback)
        self.registration_widget.check_registration_signal.connect(self.check_registration_callback)

        self.calibration_widget = CalibrationWidget()
        self.calibration_widget.state_changed.connect(self.update_calibration_settings)
        self.calibration_widget.calibration_signal.connect(self.get_pix_per_mm_callback)
        self.calibration_widget.check_calibration_signal.connect(self.check_pix_per_mm_callback)

        self.background_widget = BackgroundWidget()
        self.background_widget.state_changed.connect(self.update_background_settings)
        self.background_widget.background_signal.connect(self.background_callback)

        self.sequencer_widget = SequencerWidget()

        self.vr_settings_widget = VRSettingsWidget()
        self.vr_settings_widget.state_changed.connect(self.update_vr_settings_settings)
        self.vr_settings_widget.openloop_coords_signal.connect(self.openloop_coords_callback)

        self.output_widget = OutputWidget()
        self.output_widget.state_changed.connect(self.update_output_settings)
        self.vr_settings_widget.video_recording_signal.connect(self.output_widget.enable_video_recording)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        self.tabs.addTab(self.camera_widget, "Camera")
        self.tabs.addTab(self.projector_widget, "Projector")
        self.tabs.addTab(self.registration_widget, "Registration")
        self.tabs.addTab(self.calibration_widget, "Calibration")
        self.tabs.addTab(self.background_widget, "Background")
        self.tabs.addTab(self.sequencer_widget, "Protocol")
        self.tabs.addTab(self.vr_settings_widget, "VR")
        self.tabs.addTab(self.output_widget, "Output") 

        self.start_button = QPushButton()
        self.start_button.setText('start')
        self.start_button.clicked.connect(self.preview)

        self.stop_button = QPushButton()
        self.stop_button.setText('stop')
        self.stop_button.clicked.connect(self.stop)

        self.record_button = QPushButton()
        self.record_button.setText('record')
        self.record_button.clicked.connect(self.record)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        load_action = QAction('&Load', self)        
        load_action.setShortcut('Ctrl+O')
        load_action.setStatusTip('Load settings')
        load_action.triggered.connect(self.load_settings)

        save_action = QAction('&Save', self)        
        save_action.setShortcut('Ctrl+S')
        save_action.setStatusTip('Save settings')
        save_action.triggered.connect(self.save_settings)

        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu('&File')
        file_menu.addAction(load_action)
        file_menu.addAction(save_action)

    def layout_components(self):
        
        controls = QHBoxLayout()
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        controls.addWidget(self.record_button)

        layout = QVBoxLayout(self.main_widget)
        layout.addWidget(self.tabs)
        layout.addLayout(controls)
        layout.addStretch()

    def load_settings(self):
        # TODO restore all settings for camera (camera choice dropmenu), for protocol 
        filename, _ = QFileDialog.getOpenFileName(self, 'Open file', '', 'JSON (*.json)')
        with open(filename, 'r') as fp:
            state = json.load(fp)
        self.set_state(state)

    def save_settings(self):
        state = self.get_state()
        filename, _ = QFileDialog.getSaveFileName(self, 'Save file', '', 'JSON (*.json)')
        with open(filename, 'w') as fp:
            state = json.dump(state, fp)

    def set_state(self, state: dict) -> None:
        self.camera_widget.set_state(state['camera'])
        self.projector_widget.set_state(state['projector'])
        self.registration_widget.set_state(state['registration'])
        self.calibration_widget.set_state(state['calibration'])
        self.background_widget.set_state(state['background'])
        self.vr_settings_widget.set_state(state['vr_settings'])
        self.output_widget.set_state(state['output'])

    def get_state(self) -> dict:
        self.refresh_settings()
        return self.settings

    def update_camera_settings(self):
        self.settings['camera'] = self.camera_controller.get_state()

    def update_projector_settings(self):
        self.settings['projector'] = self.projector_widget.get_state()

    def update_registration_settings(self):
        self.settings['registration'] = self.registration_widget.get_state()

    def update_calibration_settings(self):
        self.settings['calibration'] = self.calibration_widget.get_state()

    def update_background_settings(self):
        self.settings['background'] = self.background_widget.get_state()

    def update_vr_settings_settings(self):
        self.settings['vr_settings'] = self.vr_settings_widget.get_state()

    def update_output_settings(self):
        self.settings['output'] = self.output_widget.get_state()

    def refresh_settings(self):
        self.update_camera_settings()
        self.update_projector_settings()
        self.update_registration_settings()
        self.update_calibration_settings()
        self.update_background_settings()
        self.update_vr_settings_settings()
        self.update_output_settings()
    
    def registration_callback(self):
        self.camera_controller.set_preview(False)

        p = Process(
            target = registration,
            kwargs = {
                "camera_constructor": self.camera_controller.get_constructor(),
                "cam_height": self.settings['camera']['height_value'],
                "cam_width": self.settings['camera']['width_value'],
                "cam_offset_x": self.settings['camera']['offsetX_value'],
                "cam_offset_y": self.settings['camera']['offsetY_value'], 
                "proj_width": self.settings['projector']['resolution'][0], 
                "proj_height": self.settings['projector']['resolution'][1],
                "proj_pos": self.settings['projector']['offset'],
                "pixel_scaling": self.settings['projector']['pixel_scale'],
                "exposure_microsec": self.settings['registration']['camera_exposure_ms'],
                "cam_gain": self.settings['registration']['camera_gain'], 
                "fps_bars": self.settings['registration']['bar_fps'],
                "fps_dots": self.settings['registration']['dot_fps'],
                "registration_file": self.settings['registration']['registration_file'], 
                "contrast": self.settings['registration']['image_contrast'],
                "brightness": self.settings['registration']['image_brightness'],
                "gamma": self.settings['registration']['image_gamma'],
                "blur_size_px": self.settings['registration']['blur_size_px'], 
                "dot_radius": self.settings['registration']['dot_radius_px'],
                "bar_width": self.settings['registration']['bar_width_px'],
                "bar_num_steps": self.settings['registration']['bar_step'],
                "dots_num_steps": self.settings['registration']['dot_steps'],
                "dot_detection_threshold": self.settings['registration']['detection_threshold']
            }
        )
        p.start()
        p.join()

        # update registration widget
        with open(self.settings['registration']['registration_file'],  'r') as f:
            registration_data = json.load(f)
            state = self.settings['registration']
            state['transformation_matrix'] = registration_data['cam_to_proj']
            self.registration_widget.set_state(state)
        
    def check_registration_callback(self):
        self.camera_controller.set_preview(False)

        p = Process(
            target = check_registration,
            kwargs = {
                "camera_constructor": self.camera_controller.get_constructor(),
                "cam_height": self.settings['camera']['height_value'],
                "cam_width": self.settings['camera']['width_value'],
                "cam_offset_x": self.settings['camera']['offsetX_value'],
                "cam_offset_y": self.settings['camera']['offsetY_value'],
                "proj_width": self.settings['projector']['resolution'][0],
                "proj_height": self.settings['projector']['resolution'][1],
                "proj_pos": self.settings['projector']['offset'],
                "pixel_scaling": self.settings['projector']['pixel_scale'],
                "cam_exposure_microsec": self.settings['registration']['camera_exposure_ms'],
                "cam_gain": self.settings['registration']['camera_gain'],
                "cam_fps":  self.settings['registration']['dot_fps'],
                "registration_file": self.settings['registration']['registration_file'],
                "pattern_grid_size": self.settings['registration']['pattern_grid_size'],
                "pattern_intensity": self.settings['registration']['pattern_intensity'],
            }
        )
        p.start()
        p.join()
        
    def background_callback(self):
        self.camera_controller.set_preview(False)

        if self.settings['background']['bckgsub_method'] == 'inpaint':
            p = Process(
                target = inpaint_background,
                kwargs = {
                    "camera_constructor": self.camera_controller.get_constructor(),
                    "exposure_microsec": self.settings['camera']['exposure_value'],
                    "cam_gain": self.settings['camera']['gain_value'],
                    "cam_fps": self.settings['camera']['framerate_value'],
                    "cam_height": self.settings['camera']['height_value'],
                    "cam_width": self.settings['camera']['width_value'],
                    "cam_offset_x": self.settings['camera']['offsetX_value'],
                    "cam_offset_y": self.settings['camera']['offsetY_value'],
                    "background_file": self.settings['background']['background_file'],
                    "radius": self.settings['background']['inpaint_radius'],
                    "algo": cv2.INPAINT_NS if self.settings['background']['inpaint_algo'] == 'navier-stokes' else cv2.INPAINT_TELEA
                }
            )
            p.start()
            p.join()

        elif self.settings['background']['bckgsub_method'] == 'static':
            p = Process(
                target = static_background,
                kwargs = {
                    "camera_constructor": self.camera_controller.get_constructor(),
                    "exposure_microsec": self.settings['camera']['exposure_value'],
                    "cam_gain": self.settings['camera']['gain_value'],
                    "cam_fps": self.settings['camera']['framerate_value'],
                    "cam_height": self.settings['camera']['height_value'],
                    "cam_width": self.settings['camera']['width_value'],
                    "cam_offset_x": self.settings['camera']['offsetX_value'],
                    "cam_offset_y": self.settings['camera']['offsetY_value'],
                    "background_file": self.settings['background']['background_file'],
                    "num_images": self.settings['background']['static_num_images'],
                    "time_between_images": self.settings['background']['static_pause_duration']
                }
            )
            p.start()
            p.join()

        # TODO update background widget
        image = np.load(self.settings['background']['background_file'])
        self.background_widget.set_image(image)
    
    def get_pix_per_mm_callback(self):
        self.camera_controller.set_preview(False)

        p = Process(
            target = pix_per_mm,
            kwargs = {
                "camera_constructor": self.camera_controller.get_constructor(),
                "cam_height": self.settings['camera']['height_value'],
                "cam_width": self.settings['camera']['width_value'],
                "cam_offset_x": self.settings['camera']['offsetX_value'],
                "cam_offset_y": self.settings['camera']['offsetY_value'],
                "cam_gain": self.settings['camera']['gain_value'],
                "exposure_microsec": self.settings['calibration']['camera_exposure_ms'],
                "cam_fps": self.settings['calibration']['camera_fps'],
                "checker_grid_size":  self.settings['calibration']['checkerboard_grid_size'],
                "checker_square_size_mm": self.settings['calibration']['checkerboard_square_size_mm'],
                "calibration_file": self.settings['calibration']['calibration_file']
            }
        )
        p.start()
        p.join()

        # update calibration widget pix/mm
        with open(self.settings['calibration']['calibration_file'],  'r') as f:
            pix_per_mm_val = json.load(f)
            state = self.settings['calibration']
            state['pix_per_mm'] = pix_per_mm_val
            self.calibration_widget.set_state(state)

    def check_pix_per_mm_callback(self):

        p = Process(
            target = check_pix_per_mm,
            kwargs = {
                "proj_width": self.settings['projector']['resolution'][0],
                "proj_height": self.settings['projector']['resolution'][1],
                "proj_pos": self.settings['projector']['offset'],
                "pixel_scaling": self.settings['projector']['pixel_scale'], 
                "cam_height": self.settings['camera']['height_value'],
                "cam_width": self.settings['camera']['width_value'],
                "pix_per_mm": self.settings['calibration']['pix_per_mm'],
                "thickness": self.settings['calibration']['reticle_thickness'],
                "size_to_check": self.calibration_widget.CALIBRATION_CHECK_DIAMETER_MM, # TODO make a QWidget list
                "reticle_center": self.settings['calibration']['reticle_center'],
                "registration_file": self.settings['registration']['registration_file'],
            }
        )
        p.start()
        p.join()

    def openloop_coords_callback(self):

        p = Process(
            target = open_loop_coords,
            kwargs = {
                "camera_constructor": self.camera_controller.get_constructor(),
                "exposure_microsec": self.settings['camera']['exposure_value'],
                "cam_gain": self.settings['camera']['gain_value'],
                "cam_fps": self.settings['camera']['framerate_value'],
                "cam_height": self.settings['camera']['height_value'],
                "cam_width": self.settings['camera']['width_value'],
                "cam_offset_x": self.settings['camera']['offsetX_value'],
                "cam_offset_y": self.settings['camera']['offsetY_value'],
                "openloop_file": self.settings['vr_settings']['openloop_coords_file']
            }
        )   
        p.start()
        p.join() 

        with open(self.settings['vr_settings']['openloop_coords_file'],  'r') as f:
            data = json.load(f)
            state = self.settings['vr_settings']
            state['centroid_x'] = data['centroid'][0]
            state['centroid_y'] = data['centroid'][1]
            state['heading'] = data['heading']
            self.vr_settings_widget.set_state(state)

    def start(self):
        self.camera_controller.set_preview(False)

        print(self.settings)

        if self.settings['vr_settings']['openloop']:
            self.create_open_loop_dag()
        elif self.settings['vr_settings']['videorecording']:
            self.create_video_recording_dag()
        else:
            self.create_closed_loop_dag()

        self.p_worker_logger = Process(target=self.worker_logger.run)
        self.p_queue_logger = Process(target=self.queue_logger.run)
        self.p_worker_logger.start()
        self.p_queue_logger.start()
        print('Starting DAG')
        self.dag.start()

    def stop(self):

        if self.dag is not None:
            self.dag.stop()
            print('cam to background', self.queue_cam.get_average_freq(), self.queue_cam.queue.num_lost_item.value)
            if self.settings['output']['video_recording']:
                print('cam to image saver', self.queue_save_image.get_average_freq(), self.queue_save_image.queue.num_lost_item.value)
                print('image saver to display', self.queue_display_image.get_average_freq(), self.queue_display_image.queue.num_lost_item.value)
                print('cam_to_yuv420p', self.queue_camera_to_converter.get_average_freq(), self.queue_camera_to_converter.queue.num_lost_item.value)
                print('yuv420p_to_saver', self.queue_converter_to_saver.get_average_freq(), self.queue_converter_to_saver.queue.num_lost_item.value)
            print('background to trackers', self.queue_background.get_average_freq(), self.queue_background.queue.num_lost_item.value)
            print('trackers to visual stim', self.queue_tracking.get_average_freq(), self.queue_tracking.queue.num_lost_item.value)
            print('trackers to display', self.queue_overlay.get_average_freq(), self.queue_overlay.queue.num_lost_item.value)
            self.worker_logger.stop()
            self.queue_logger.stop()
            self.p_worker_logger.join()
            self.p_queue_logger.join()
            print('DAG stopped')

    def preview(self):
        # maybe launch preview in QThread to prevent window from hanging

        self.record_flag = False
        self.start()
        
    def record(self):
        # maybe launch record in QThread to prevent window from hanging
        # TODO make sleep interruptible by stop ? 

        self.camera_controller.set_preview(False)

        self.record_flag = True
        self.start() #TODO initialization takes ~5secs. It would be nice to take account of this for sleep duration
        time.sleep(self.sequencer_widget.get_protocol_duration()) 
        self.stop()

    def closeEvent(self, event):
        # close all widgets. Ensures that cleanup logic defined in closeEvent 
        # is executed
        self.camera_widget.close()
        self.projector_widget.close()
        self.registration_widget.close()
        self.calibration_widget.close()
        self.background_widget.close()
        self.sequencer_widget.close()
        self.vr_settings_widget.close()
        self.output_widget.close()