from multiprocessing import Process
from multiprocessing_logger import Logger
from dagline import ProcessingDAG
import time
from typing import Dict
from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QPushButton,
    QTabWidget
)
from PyQt5.QtGui import QIcon
from ZebVR.widgets import SequencerWidget
from ZebVR.calibration import (
    check_pix_per_mm, 
    check_registration, 
    open_loop_coords, 
    pix_per_mm, 
    registration
)
from ZebVR.background import inpaint_background, static_background

from ZebVR.config import *
from ZebVR.widgets import (
    CameraWidget, 
    ProjectorWidget, 
    RegistrationWidget,
    CalibrationWidget,
    BackgroundWidget,
    OpenLoopWidget,
    OutputWidget
)
from functools import partial

try:
    from camera_tools import XimeaCamera
    XIMEA_ENABLED = True
except ImportError:
    XIMEA_ENABLED = False
    
class MainGui(QWidget):
    
    def __init__(self, workers: Dict, queues: Dict, worker_logger: Logger, queue_logger: Logger, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.camera_constructor = None
        self.settings = {}
        self.dag = None
        self.workers = workers
        self.queues = queues
        self.worker_logger = worker_logger
        self.queue_logger = queue_logger
        self.record_flag = False
        
        self.create_components()
        self.layout_components()

        self.update_camera_settings()
        self.update_projector_settings()
        self.update_registration_settings()
        self.update_calibration_settings()
        self.update_background_settings()
        self.update_openloop_settings()
        self.update_output_settings()

        self.setWindowTitle('ZebVR')
        self.setWindowIcon(QIcon('ZebVR/resources/zebvr.png'))

    def create_open_loop_dag(self):

        # clear workers and queues

        for key, worker in self.workers.items():
            worker.reset()

        for key, queue in self.queues.items():
            queue.clear()

        self.dag = ProcessingDAG()

        if self.filename is not None:
            self.workers['visual_stim'].set_filename(self.edt_filename.text())

        for i in range(N_TRACKER_WORKERS):
            self.dag.connect_data(
                sender=self.workers[f'tracker_{i}'], 
                receiver=self.workers['visual_stim'], 
                queue=self.queues['tracker_to_stim'], 
                name='stimulus'
            )

        if self.record_flag:
            protocol = self.sequencer_widget.get_protocol()
            self.workers['protocol'].set_protocol(protocol)
            self.dag.connect_metadata(
                sender=self.workers['protocol'], 
                receiver=self.workers['visual_stim'], 
                queue=self.queues['visual_stim_control'], 
                name='visual_stim_control'
            )
        else:
            self.dag.connect_metadata(
                sender=self.workers['visual_stim_control'], 
                receiver=self.workers['visual_stim'], 
                queue=self.queues['visual_stim_control'], 
                name='visual_stim_control'
            )
            

    def create_closed_loop_dag(self):

        # clear workers and queues

        for key, worker in self.workers.items():
            worker.reset()

        for key, queue in self.queues.items():
            queue.clear()

        self.dag = ProcessingDAG()

        # data
        for i in range(N_BACKGROUND_WORKERS):   
            self.dag.connect_data(
                sender=self.workers['camera'], 
                receiver=self.workers[f'background_{i}'], 
                queue=self.queues['camera_to_background'], 
                name='background_subtraction'
            )
        
        # NOTE: the order in which you declare connections matter: background_subtraction will
        # be served before image_saver
        if RECORD_VIDEO:
            self.dag.connect_data(
                sender=self.workers['camera'], 
                receiver=self.workers['video_recorder'], 
                queue=self.queues['camera_to_video_recorder'], 
                name='image_saver'
            )

        for i in range(N_BACKGROUND_WORKERS):
            for j in range(N_TRACKER_WORKERS):
                self.dag.connect_data(
                    sender=self.workers[f'background_{i}'], 
                    receiver=self.workers[f'tracker_{j}'], 
                    queue=self.queues['background_to_tracker'], 
                    name='background_subtracted'
                )


        for i in range(N_TRACKER_WORKERS):
            self.dag.connect_data(
                sender=self.workers[f'tracker_{i}'], 
                receiver=self.workers['tracking_display'], 
                queue=self.queues['tracker_to_tracking_display'], 
                name='overlay'
            )

        if self.filename is not None:
            self.workers['visual_stim'].set_filename(self.edt_filename.text())

        for i in range(N_TRACKER_WORKERS):
            self.dag.connect_data(
                sender=self.workers[f'tracker_{i}'], 
                receiver=self.workers['visual_stim'], 
                queue=self.queues['tracker_to_stim'], 
                name='stimulus'
            )

        # metadata
        self.dag.connect_metadata(
            sender=self.workers['camera_gui'], 
            receiver=self.workers['camera'], 
            queue=self.queues['camera_control_to_camera'], 
            name='camera_control'
        )
        
        self.dag.connect_metadata(
            sender=self.workers['camera'], 
            receiver=self.workers['camera_gui'], 
            queue=self.queues['camera_to_camera_control'], 
            name='camera_info'
        )

        if self.record_flag:
            protocol = self.sequencer_widget.get_protocol()
            self.workers['protocol'].set_protocol(protocol)
            self.dag.connect_metadata(
                sender=self.workers['protocol'], 
                receiver=self.workers['visual_stim'], 
                queue=self.queues['visual_stim_control'], 
                name='visual_stim_control'
            )
        else:
            self.dag.connect_metadata(
                sender=self.workers['visual_stim_control'], 
                receiver=self.workers['visual_stim'], 
                queue=self.queues['visual_stim_control'], 
                name='visual_stim_control'
            )
            
        for i in range(N_TRACKER_WORKERS):
            self.dag.connect_metadata(
                sender=self.workers['tracker_gui'], 
                receiver=self.workers[f'tracker_{i}'], 
                queue=self.queues[f'tracker_control_to_tracker_{i}'], 
                name=f'tracker_control_{i}'
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

        self.openloop_widget = OpenLoopWidget()
        self.openloop_widget.state_changed.connect(self.update_openloop_settings)
        self.openloop_widget.openloop_signal.connect(self.open_loop_coords_callback)

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
        self.tabs.addTab(self.openloop_widget, "VR")
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

    def layout_components(self):
        
        controls = QHBoxLayout()
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        controls.addWidget(self.record_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tabs)
        layout.addLayout(controls)
        layout.addStretch()

    def update_camera_source(self, cam_source: str, cam_ind: int, filename: str):

        if cam_source=='Webcam':
            self.camera_constructor = partial(OpenCV_Webcam, cam_id=cam_ind)

        elif cam_source=='Movie':
            self.camera_constructor = partial(MovieFileCam, filename=filename)

        elif cam_source=='XIMEA' and XIMEA_ENABLED:
            self.camera_constructor = partial(XimeaCamera, dev_id=cam_ind)

    def camera_preview(self):
        pass

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

    def update_openloop_settings(self):
        self.settings['openloop'] = self.openloop_widget.get_state()

    def update_output_settings(self):
        self.settings['output'] = self.output_widget.get_state()

    def registration_callback(self):
        p = Process(
            target = registration,
            kwargs = {
                "camera_constructor": CAMERA_CONSTRUCTOR,
                "exposure_microsec": CAM_REGISTRATION_EXPOSURE_MS,
                "cam_height": CAM_HEIGHT,
                "cam_width": CAM_WIDTH,
                "cam_gain": CAM_GAIN,
                "fps_bars": CAM_REGISTRATION_BARS_FPS,
                "fps_dots": CAM_REGISTRATION_DOTS_FPS,
                "cam_offset_x": CAM_OFFSETX,
                "cam_offset_y": CAM_OFFSETY,
                "proj_width": PROJ_WIDTH,
                "proj_height": PROJ_HEIGHT,
                "proj_pos": PROJ_POS,
                "registration_file": REGISTRATION_FILE, 
                "contrast": CONTRAST,
                "brightness": BRIGHTNESS,
                "gamma": GAMMA,
                "blur_size_px": BLUR_SIZE_PX,
                "dot_radius": DOT_RADIUS,
                "bar_num_steps": BAR_STEPS,
                "dots_num_steps": DOT_STEPS,
                "dot_detection_threshold": DETECTION_THRESHOLD,
                "pixel_scaling": PIXEL_SCALING
            }
        )
        p.start()
        p.join()
        
    def check_registration_callback(self):
        p = Process(
            target = check_registration,
            kwargs = {
                "camera_constructor": CAMERA_CONSTRUCTOR,
                "cam_exposure_microsec": CAM_EXPOSURE_MS,
                "cam_gain": CAM_GAIN,
                "cam_fps": CAM_FPS,
                "cam_height": CAM_HEIGHT,
                "cam_width": CAM_WIDTH,
                "cam_offset_x": CAM_OFFSETX,
                "cam_offset_y": CAM_OFFSETY,
                "proj_width": PROJ_WIDTH,
                "proj_height": PROJ_HEIGHT,
                "proj_pos": PROJ_POS,
                "registration_file": REGISTRATION_FILE,
                "pattern_grid_size": 5,
                "pattern_intensity": PATTERN_INTENSITY,
                "pixel_scaling": PIXEL_SCALING
            }
        )
        p.start()
        p.join()
        
    def background_callback(self):

        if self.background_method.currentText() == 'inpaint':
            p = Process(
                target = inpaint_background,
                kwargs = {
                    "camera_constructor": CAMERA_CONSTRUCTOR,
                    "exposure_microsec": CAM_EXPOSURE_MS,
                    "cam_gain": CAM_GAIN,
                    "cam_fps": CAM_FPS,
                    "cam_height": CAM_HEIGHT,
                    "cam_width": CAM_WIDTH,
                    "cam_offset_x": CAM_OFFSETX,
                    "cam_offset_y": CAM_OFFSETY,
                    "background_file": BACKGROUND_FILE
                }
            )
            p.start()
            p.join()

        elif self.background_method.currentText() == 'static':
            p = Process(
                target = static_background,
                kwargs = {
                    "camera_constructor": CAMERA_CONSTRUCTOR,
                    "exposure_microsec": CAM_EXPOSURE_MS,
                    "cam_gain": CAM_GAIN,
                    "cam_fps": CAM_FPS,
                    "cam_height": CAM_HEIGHT,
                    "cam_width": CAM_WIDTH,
                    "cam_offset_x": CAM_OFFSETX,
                    "cam_offset_y": CAM_OFFSETY,
                    "background_file": BACKGROUND_FILE,
                    "num_images": NUM_IMAGES,
                    "time_between_images": TIME_BETWEEN_IMAGES
                }
            )
            p.start()
            p.join()
    
    def get_pix_per_mm_callback(self):
        
        p = Process(
            target = pix_per_mm,
            kwargs = {
                "camera_constructor": CAMERA_CONSTRUCTOR,
                "exposure_microsec": CALIBRATION_CAM_EXPOSURE_MS,
                "cam_gain": CAM_GAIN,
                "cam_fps": CALIBRATION_CAM_FPS,
                "cam_height": CAM_HEIGHT,
                "cam_width": CAM_WIDTH,
                "cam_offset_x": CAM_OFFSETX,
                "cam_offset_y": CAM_OFFSETY,
                "checker_grid_size": CALIBRATION_CHECKER_SIZE,
                "checker_square_size_mm": CALIBRATION_SQUARE_SIZE_MM
            }
        )
        p.start()
        p.join()

    def check_pix_per_mm_callback(self):

        p = Process(
            target = check_pix_per_mm,
            kwargs = {
                "proj_width": PROJ_WIDTH,
                "proj_height": PROJ_HEIGHT,
                "proj_pos": PROJ_POS,
                "cam_height": CAM_HEIGHT,
                "cam_width": CAM_WIDTH,
                "pix_per_mm": PIX_PER_MM,
                "size_to_check": CALIBRATION_CHECK_DIAMETER_MM,
                "registration_file": REGISTRATION_FILE,
                "thickness": 10.0,
                "pixel_scaling": PIXEL_SCALING, 
            }
        )
        p.start()
        p.join()

    def open_loop_coords_callback(self):

        p = Process(
            target = open_loop_coords,
            kwargs = {
                "camera_constructor": CAMERA_CONSTRUCTOR,
                "exposure_microsec": CAM_EXPOSURE_MS,
                "cam_gain": CAM_GAIN,
                "cam_fps": CAM_FPS,
                "cam_height": CAM_HEIGHT,
                "cam_width": CAM_WIDTH,
                "cam_offset_x": CAM_OFFSETX,
                "cam_offset_y": CAM_OFFSETY,
                "openloop_file": OPEN_LOOP_DATAFILE
            }
        )   
        p.start()
        p.join() 

    def start(self):
        if OPEN_LOOP:
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
            print('cam to background', self.queues['camera_to_background'].get_average_freq(), self.queues['camera_to_background'].queue.num_lost_item.value)
            if RECORD_VIDEO:
                print('cam to image saver', self.queues['camera_to_video_recorder'].get_average_freq(), self.queues['camera_to_video_recorder'].queue.num_lost_item.value)
            print('background to trackers', self.queues['background_to_tracker'].get_average_freq(), self.queues['background_to_tracker'].queue.num_lost_item.value)
            print('trackers to visual stim', self.queues['tracker_to_stim'].get_average_freq(), self.queues['tracker_to_stim'].queue.num_lost_item.value)
            print('trackers to display', self.queues['tracker_to_tracking_display'].get_average_freq(), self.queues['tracker_to_tracking_display'].queue.num_lost_item.value)
            self.worker_logger.stop()
            self.queue_logger.stop()
            self.p_worker_logger.join()
            self.p_queue_logger.join()
            print('DAG stopped')

    def preview(self):
        self.record_flag = False
        self.start()
        
    def record(self):
        self.record_flag = True
        self.start()
        time.sleep(self.duration.value())
        self.stop()