from multiprocessing import Process
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
from PyQt5.QtCore import  QRunnable, QThreadPool
from functools import partial
import json
import cv2

from multiprocessing_logger import Logger
from image_tools import im2gray
from dagline import ProcessingDAG
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

from camera_tools import Camera, OpenCV_Webcam_InitEveryFrame
try:
    from camera_tools import XimeaCamera
    XIMEA_ENABLED = True
except ImportError:
    XIMEA_ENABLED = False

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
                    self.widget.set_image(im2gray(frame['image']))
            except:
                pass
        self.camera.stop_acquisition()
        
class MainGui(QWidget):
    
    def __init__(self, workers: Dict, queues: Dict, worker_logger: Logger, queue_logger: Logger, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.camera = None
        self.camera_constructor = None
        self.thread_pool = QThreadPool()
        self.acq = None
        self.camera_preview_started = False

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

    def update_openloop_settings(self):
        self.settings['openloop'] = self.openloop_widget.get_state()

    def update_output_settings(self):
        self.settings['output'] = self.output_widget.get_state()

    def registration_callback(self):
        if self.camera_preview_started:
            self.camera_preview_started = False
            self.acq.stop()

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
        if self.camera_preview_started:
            self.camera_preview_started = False
            self.acq.stop()

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
        if self.camera_preview_started:
            self.camera_preview_started = False
            self.acq.stop()

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

        # TODO update calibration widget

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

        # TODO update openloop widget

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