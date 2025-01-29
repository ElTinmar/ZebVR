from multiprocessing import Process
import time
import json
import pickle
import pprint

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
from ZebVR.calibration import (
    check_pix_per_mm, 
    check_registration, 
    open_loop_coords, 
    pix_per_mm, 
    registration
)
from ZebVR.background import inpaint_background, static_background
from ZebVR.widgets import (
    CameraWidget, CameraController,
    ProjectorWidget, ProjectorController,
    RegistrationWidget,
    CalibrationWidget,
    BackgroundWidget,
    VRSettingsWidget,
    OutputWidget,
    SequencerWidget
)
from ZebVR.dags import closed_loop, open_loop, video_recording, tracking

PROFILE = False
        
class MainGui(QMainWindow):
    
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.settings = {}
        self.settings['main'] = {}
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

        self.setWindowTitle('ZebVR')
        self.setWindowIcon(QIcon('ZebVR/resources/zebvr.png'))

    def create_components(self):

        self.camera_widget = CameraWidget()
        self.camera_controller = CameraController(self.camera_widget)
        self.camera_controller.state_changed.connect(self.update_camera_settings)

        self.projector_widget = ProjectorWidget()
        self.projector_controller = ProjectorController(self.projector_widget)
        self.projector_controller.state_changed.connect(self.update_projector_settings)

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
        self.sequencer_widget.state_changed.connect(self.update_protocol_settings)

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
        filename, _ = QFileDialog.getOpenFileName(self, 'Open file', '', 'VR Settings (*.vr)')
        with open(filename, 'rb') as fp:
            state = pickle.load(fp)
        self.set_state(state)

    def save_settings(self):
        state = self.get_state()
        filename, _ = QFileDialog.getSaveFileName(self, 'Save file', '', 'VR Settings (*.vr)')
        with open(filename, 'wb') as fp:
            state = pickle.dump(state, fp)

    def set_state(self, state: dict) -> None:
        self.camera_widget.set_state(state['camera'])
        self.projector_widget.set_state(state['projector'])
        self.registration_widget.set_state(state['registration'])
        self.calibration_widget.set_state(state['calibration'])
        self.background_widget.set_state(state['background'])
        self.vr_settings_widget.set_state(state['vr_settings'])
        self.output_widget.set_state(state['output'])
        self.sequencer_widget.set_protocol(state['protocol'])

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

    def update_protocol_settings(self):
        self.settings['protocol'] = self.sequencer_widget.get_protocol()

    def refresh_settings(self):
        self.update_camera_settings()
        self.update_projector_settings()
        self.update_registration_settings()
        self.update_calibration_settings()
        self.update_background_settings()
        self.update_vr_settings_settings()
        self.update_output_settings()
        self.update_protocol_settings()
    
    def registration_callback(self):
        self.camera_controller.set_preview(False)

        p = Process(
            target = registration,
            kwargs = {
                "camera_constructor": self.settings['camera']['camera_constructor'],
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
                "camera_constructor": self.settings['camera']['camera_constructor'],
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
                    "camera_constructor": self.settings['camera']['camera_constructor'],
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
                    "camera_constructor": self.settings['camera']['camera_constructor'],
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
                "camera_constructor": self.settings['camera']['camera_constructor'],
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
                "camera_constructor": self.settings['camera']['camera_constructor'],
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

        pprint.pprint(self.settings)

        if self.settings['vr_settings']['openloop']:
            self.dag, self.worker_logger, self.queue_logger = open_loop(self.settings)
        elif self.settings['vr_settings']['videorecording']:
            self.dag, self.worker_logger, self.queue_logger = video_recording(self.settings)
        elif self.settings['vr_settings']['tracking']:
            self.dag, self.worker_logger, self.queue_logger = tracking(self.settings)
        else:
            self.dag, self.worker_logger, self.queue_logger = closed_loop(self.settings)

        self.p_worker_logger = Process(target=self.worker_logger.run)
        self.p_queue_logger = Process(target=self.queue_logger.run)
        self.p_worker_logger.start()
        self.p_queue_logger.start()
        print('Starting DAG')
        self.dag.start()

    def stop(self):

        if self.dag is not None:
            self.dag.stop()
            self.worker_logger.stop()
            self.queue_logger.stop()
            self.p_worker_logger.join()
            self.p_queue_logger.join()
            print('DAG stopped')

    def preview(self):
        # maybe launch preview in QThread to prevent window from hanging

        self.settings['main']['record'] = False
        self.start()
        
    def record(self):
        # maybe launch record in QThread to prevent window from hanging
        # TODO make sleep interruptible by stop ? 

        self.camera_controller.set_preview(False)

        self.settings['main']['record'] = True
        self.start() 
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