from multiprocessing import Process
import time
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
from PyQt5.QtCore import  QRunnable, QThreadPool
from functools import partial
import json
import cv2
import numpy as np
import os

from multiprocessing_logger import Logger
from dagline import ProcessingDAG, receive_strategy, send_strategy
from ZebVR.widgets import SequencerWidget
from ZebVR.calibration import (
    check_pix_per_mm, 
    check_registration, 
    open_loop_coords, 
    pix_per_mm, 
    registration
)
from ZebVR.background import inpaint_background, static_background
from ZebVR.widgets import (
    CameraWidget, 
    ProjectorWidget, 
    RegistrationWidget,
    CalibrationWidget,
    BackgroundWidget,
    VRSettingsWidget,
    OutputWidget
)
from ZebVR.workers import (
    BackgroundSubWorker, 
    CameraWorker, 
    TrackerWorker, 
    DummyTrackerWorker,
    ImageSaverWorker, 
    TrackerGui, 
    StimGUI,
    TrackingDisplay,
    Protocol
)
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
from ZebVR.stimulus import VisualStimWorker, GeneralStim

from camera_tools import Camera, OpenCV_Webcam, OpenCV_Webcam_InitEveryFrame, MovieFileCam
try:
    from camera_tools import XimeaCamera
    XIMEA_ENABLED = True
except ImportError:
    XIMEA_ENABLED = False

PROFILE = False

class CameraAcquisition(QRunnable):

    def __init__(self, camera: Camera, widget: CameraWidget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.camera = camera
        self.widget = widget
        self.keepgoing = True
        
    def stop(self):
        self.keepgoing = False
    
    def run(self):
        self.camera.start_acquisition()
        while self.keepgoing:
            try:
                frame = self.camera.get_frame()
                if frame['image'] is not None:
                    self.widget.set_image(frame['image'])
            except:
                pass
        self.camera.stop_acquisition()
        
class MainGui(QMainWindow):
    
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.camera = None
        self.camera_constructor = None
        self.thread_pool = QThreadPool()
        self.acq = None
        self.camera_preview_started = False
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

        self.update_camera_settings()
        self.update_projector_settings()
        self.update_registration_settings()
        self.update_calibration_settings()
        self.update_background_settings()
        self.update_vr_settings_settings()
        self.update_output_settings()

        self.create_loggers()

        self.setWindowTitle('ZebVR')
        self.setWindowIcon(QIcon('ZebVR/resources/zebvr.png'))

    def create_loggers(self):
        
        self.worker_logger = Logger(self.settings['output']['worker_logfile'], Logger.INFO)
        self.queue_logger = Logger(self.settings['output']['queue_logfile'], Logger.INFO)

    def create_workers(self):

        # camera --------------------------------------------------
        self.camera_worker = CameraWorker(
            camera_constructor = self.camera_constructor, 
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
            fps = self.settings['output']['video_recording_fps'],
            compress = self.settings['output']['video_recording_compression'],
            resize = self.settings['output']['video_recording_resize'],
            name = 'image_saver',  
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

        self.queue_save_image = MonitoredQueue(
            ModifiableRingBuffer(
                num_bytes = 500*1024**2,
                logger = self.queue_logger,
                name = 'camera_to_image_saver',
                t_refresh = 1e-6 * self.settings['vr_settings']['queue_refresh_time_microsec']
            )
        )

        self.queue_background = MonitoredQueue(
            ModifiableRingBuffer(
                num_bytes = 500*1024**2,
                copy=False, # you probably don't need to copy if processing is fast enough
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

    def create_open_loop_dag(self):

        # clear workers and queues
        self.create_workers()
        self.create_queues()

        self.dag = ProcessingDAG()

        for i in range(self.settings['vr_settings']['n_tracker_workers']):
            self.dag.connect_data(
                sender = self.tracker_worker_list[i], 
                receiver = self.stim_worker, 
                queue = self.queue_tracking, 
                name = 'stimulus'
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
            

    def create_closed_loop_dag(self):

        # clear workers and queues
        self.create_workers()
        self.create_queues()

        self.dag = ProcessingDAG()

        # data
        for i in range(self.settings['vr_settings']['n_background_workers']):   
            self.dag.connect_data(
                sender = self.camera_worker, 
                receiver = self.background_worker_list[i], 
                queue = self.queue_cam, 
                name='background_subtraction'
            )
        
        # NOTE: the order in which you declare connections matter: background_subtraction will
        # be served before image_saver
        if self.settings['output']['video_recording']:
            self.dag.connect_data(
                sender = self.camera_worker, 
                receiver = self.image_saver_worker, 
                queue = self.queue_save_image, 
                name = 'image_saver'
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
                name = 'overlay'
            )

        for i in range(self.settings['vr_settings']['n_tracker_workers']):
            self.dag.connect_data(
                sender = self.tracker_worker_list[i], 
                receiver = self.stim_worker, 
                queue = self.queue_tracking, 
                name = 'stimulus'
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

    def create_components(self):

        self.camera_widget = CameraWidget()
        self.camera_widget.state_changed.connect(self.update_camera_settings)
        self.camera_widget.camera_source.connect(self.update_camera_source)
        self.camera_widget.preview.connect(self.camera_preview)

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
        return self.settings

    def update_camera_source(self, cam_source: str, cam_ind: int, filename: str):

        if cam_source=='Webcam':
            self.camera_constructor = partial(OpenCV_Webcam, cam_id=cam_ind)
        
        elif cam_source=='Webcam (Registration Mode)':
            self.camera_constructor = partial(OpenCV_Webcam_InitEveryFrame, cam_id=cam_ind)

        elif cam_source=='Movie' and os.path.exists(filename):
            self.camera_constructor = partial(MovieFileCam, filename=filename)

        elif cam_source=='XIMEA' and XIMEA_ENABLED:
            self.camera_constructor = partial(XimeaCamera, dev_id=cam_ind)

        self.camera = self.camera_constructor()

        # read camera properties and set widget state accordingly
        state = {}
        
        framerate_enabled = self.camera.framerate_available()
        state['framerate_enabled'] = framerate_enabled
        state['framerate_min'], state['framerate_max'] = self.camera.get_framerate_range() if framerate_enabled else (0,0)
        state['framerate_step'] = self.camera.get_framerate_increment() if framerate_enabled else 0
        state['framerate_value'] = self.camera.get_framerate() if framerate_enabled else 0

        gain_enabled = self.camera.gain_available()
        state['gain_enabled'] = gain_enabled
        state['gain_min'], state['gain_max'] = self.camera.get_gain_range() if gain_enabled else (0,0)
        state['gain_step'] = self.camera.get_gain_increment() if gain_enabled else 0
        state['gain_value'] = self.camera.get_gain() if gain_enabled else 0

        exposure_enabled = self.camera.exposure_available()
        state['exposure_enabled'] = exposure_enabled
        state['exposure_min'], state['exposure_max'] = self.camera.get_exposure_range() if exposure_enabled else (0,0)
        state['exposure_step'] = self.camera.get_exposure_increment() if exposure_enabled else 0
        state['exposure_value'] = self.camera.get_exposure() if exposure_enabled else 0

        offsetX_enabled = self.camera.offsetX_available()
        state['offsetX_enabled'] = offsetX_enabled
        state['offsetX_min'], state['offsetX_max'] = self.camera.get_offsetX_range() if offsetX_enabled else (0,0)
        state['offsetX_step'] = self.camera.get_offsetX_increment() if offsetX_enabled else 0
        state['offsetX_value'] = self.camera.get_offsetX() if offsetX_enabled else 0

        offsetY_enabled = self.camera.offsetY_available()
        state['offsetY_enabled'] = offsetY_enabled
        state['offsetY_min'], state['offsetY_max'] = self.camera.get_offsetY_range() if offsetY_enabled else (0,0)
        state['offsetY_step'] = self.camera.get_offsetY_increment() if offsetY_enabled else 0
        state['offsetY_value'] = self.camera.get_offsetY() if offsetY_enabled else 0

        height_enabled = self.camera.height_available()
        state['height_enabled'] = height_enabled
        state['height_min'], state['height_max'] = self.camera.get_height_range() if height_enabled else (0,0)
        state['height_step'] = self.camera.get_height_increment() if height_enabled else 0
        state['height_value'] = self.camera.get_height() if height_enabled else 0

        width_enabled = self.camera.width_available()
        state['width_enabled'] = width_enabled
        state['width_min'], state['width_max'] = self.camera.get_width_range() if width_enabled else (0,0)
        state['width_step'] = self.camera.get_width_increment() if width_enabled else 0
        state['width_value'] = self.camera.get_width() if width_enabled else 0
        
        self.camera_widget.set_state(state)

    def camera_preview(self, enable: bool):
        if enable:
            if not self.camera_preview_started:
                self.camera_preview_started = True
                self.acq = CameraAcquisition(self.camera, self.camera_widget)
                self.thread_pool.start(self.acq)
        else:
            if self.camera_preview_started:
                self.camera_preview_started = False
                self.acq.stop()

    def update_camera_settings(self):
        self.settings['camera'] = self.camera_widget.get_state()

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

    def registration_callback(self):
        self.camera_preview(False)

        p = Process(
            target = registration,
            kwargs = {
                "camera_constructor": self.camera_constructor,
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
        self.camera_preview(False)

        p = Process(
            target = check_registration,
            kwargs = {
                "camera_constructor": self.camera_constructor,
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
        self.camera_preview(False)

        if self.settings['background']['bckgsub_method'] == 'inpaint':
            p = Process(
                target = inpaint_background,
                kwargs = {
                    "camera_constructor": self.camera_constructor,
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
                    "camera_constructor": self.camera_constructor,
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
        self.camera_preview(False)

        p = Process(
            target = pix_per_mm,
            kwargs = {
                "camera_constructor": self.camera_constructor,
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
                "camera_constructor": self.camera_constructor,
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
        self.camera_preview(False)

        print(self.settings)

        if self.settings['vr_settings']['openloop']:
            self.create_open_loop_dag()
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

        self.camera_preview(False)

        self.record_flag = True
        self.start() #TODO initialization takes ~5secs. It would be nice to take account of this for sleep duration
        time.sleep(self.sequencer_widget.get_protocol_duration()) 
        self.stop()