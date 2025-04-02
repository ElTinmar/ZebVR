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
    QButtonGroup,
    QFileDialog,
    QSizePolicy
)
from PyQt5.QtGui import QIcon
from .calibration import (
    check_pix_per_mm, 
    check_registration, 
    pix_per_mm, 
    registration
)
from .background import inpaint_background, static_background
from qt_widgets import LabeledDoubleSpinBox
from .widgets import (
    CameraWidget, CameraController,
    ProjectorWidget, ProjectorController,
    RegistrationWidget,
    CalibrationWidget,
    BackgroundWidget,
    IdentityWidget,
    SequencerWidget,
    SettingsWidget,
    LogsWidget
)
from .dags import closed_loop, open_loop, video_recording, tracking
        
class MainGui(QMainWindow):
    
    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.settings = {}
        self.settings['main'] = {}

        self.dag = None
        self.worker_logger = None
        self.queue_logger = None

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

        self.identity_widget = IdentityWidget()
        self.identity_widget.state_changed.connect(self.update_identity_settings)

        self.sequencer_widget = SequencerWidget()
        self.sequencer_widget.state_changed.connect(self.update_sequencer_settings)

        self.settings_widget = SettingsWidget()
        self.settings_widget.state_changed.connect(self.update_settings)

        self.logs_widget = LogsWidget()
        self.logs_widget.state_changed.connect(self.update_logs)
        
        self.close_loop_button = QPushButton('Close-loop')
        self.close_loop_button.setCheckable(True)
        self.open_loop_button = QPushButton('Open-loop')
        self.open_loop_button.setCheckable(True)
        self.video_recording_button = QPushButton('Record Video')
        self.video_recording_button.setCheckable(True)
        self.tracking_button = QPushButton('Track')
        self.tracking_button.setCheckable(True)
        self.top_buttons = QButtonGroup()
        self.top_buttons.addButton(self.close_loop_button)
        self.top_buttons.addButton(self.open_loop_button)
        self.top_buttons.addButton(self.video_recording_button)
        self.top_buttons.addButton(self.tracking_button)
        self.top_buttons.setExclusive(True)
        self.top_buttons.buttonClicked.connect(self.top_button_changed)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        self.tabs.addTab(self.camera_widget, "Camera")
        self.tabs.addTab(self.projector_widget, "Projector")
        self.tabs.addTab(self.registration_widget, "Registration")
        self.tabs.addTab(self.calibration_widget, "Calibration")
        self.tabs.addTab(self.background_widget, "Background")
        self.tabs.addTab(self.identity_widget, "Identity")
        self.tabs.addTab(self.sequencer_widget, "Protocol")
        self.tabs.addTab(self.settings_widget, "Settings")
        self.tabs.addTab(self.logs_widget, "Logs") 
        self.tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding) 

        self.start_button = QPushButton()
        self.start_button.setText('start')
        self.start_button.clicked.connect(self.preview)

        self.stop_button = QPushButton()
        self.stop_button.setText('stop')
        self.stop_button.clicked.connect(self.stop)

        self.record_button = QPushButton()
        self.record_button.setText('record')
        self.record_button.clicked.connect(self.record)

        self.recording_duration = LabeledDoubleSpinBox()
        self.recording_duration.setText('recording duration (s)')
        self.recording_duration.setRange(0,100_000)
        self.recording_duration.setValue(0)
        self.recording_duration.valueChanged.connect(self.update_main_settings)

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

        self.close_loop_button.click()

    def layout_components(self) -> None:

        top_buttons = QHBoxLayout()
        top_buttons.addWidget(self.close_loop_button)
        top_buttons.addWidget(self.open_loop_button)
        top_buttons.addWidget(self.video_recording_button)
        top_buttons.addWidget(self.tracking_button)
        
        controls = QHBoxLayout()
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
       
        record = QHBoxLayout()
        record.addWidget(self.recording_duration)
        record.addWidget(self.record_button)

        layout = QVBoxLayout(self.main_widget)
        layout.addLayout(top_buttons)
        layout.addWidget(self.tabs)
        layout.addLayout(controls)
        layout.addLayout(record)

    def set_tab_visibililty(self, widgets_to_show, widgets_to_hide):

        for w in widgets_to_show:
                index = self.tabs.indexOf(w)
                self.tabs.setTabVisible(index, True)
            
        for w in widgets_to_hide:
            index = self.tabs.indexOf(w)
            self.tabs.setTabVisible(index, False)

    def top_button_changed(self):

        # show only relevant settings for the current mode
        if self.close_loop_button.isChecked():

            widgets_to_show = [
                self.camera_widget,
                self.projector_widget, 
                self.calibration_widget, 
                self.background_widget,
                self.identity_widget, 
                self.registration_widget,
                self.sequencer_widget,
                self.settings_widget
            ]

            widgets_to_hide = []

            self.set_tab_visibililty(widgets_to_show, widgets_to_hide)
            self.settings_widget.set_tracking_visible(True)
            self.settings_widget.force_videorecording(False)
            self.settings_widget.set_stim_output_visible(True)
            self.identity_widget.set_open_loop_visible(False)

        elif self.open_loop_button.isChecked():

            widgets_to_show = [
                self.camera_widget,
                self.projector_widget,
                self.calibration_widget,
                self.registration_widget,
                self.sequencer_widget,
                self.settings_widget,
                self.background_widget,
                self.identity_widget
            ]

            widgets_to_hide = []

            self.set_tab_visibililty(widgets_to_show, widgets_to_hide)
            self.settings_widget.set_tracking_visible(False)
            self.settings_widget.force_videorecording(False)
            self.settings_widget.set_stim_output_visible(True)
            self.identity_widget.set_open_loop_visible(True)

        elif self.video_recording_button.isChecked():

            widgets_to_show = [
                self.camera_widget,
                self.settings_widget
            ]

            widgets_to_hide = [
                self.projector_widget, 
                self.calibration_widget, 
                self.background_widget,
                self.identity_widget,
                self.registration_widget,
                self.sequencer_widget
            ]

            self.set_tab_visibililty(widgets_to_show, widgets_to_hide)
            self.settings_widget.set_tracking_visible(False)
            self.settings_widget.force_videorecording(True)
            self.settings_widget.set_stim_output_visible(False)
            self.identity_widget.set_open_loop_visible(False)

        elif self.tracking_button.isChecked():
            
            widgets_to_show = [
                self.camera_widget,
                self.background_widget, 
                self.identity_widget,
                self.settings_widget
            ]

            widgets_to_hide = [
                self.registration_widget,
                self.calibration_widget,
                self.projector_widget, 
                self.sequencer_widget
            ]

            self.set_tab_visibililty(widgets_to_show, widgets_to_hide)
            self.settings_widget.set_tracking_visible(True)
            self.settings_widget.force_videorecording(False)
            self.settings_widget.set_stim_output_visible(False)
            self.identity_widget.set_open_loop_visible(False)

        else:
            raise RuntimeError       

    def load_settings(self):
        filename, _ = QFileDialog.getOpenFileName(self, 'Open file', '', 'VR Settings (*.vr)')
        try:
            with open(filename, 'rb') as fp:
                state = pickle.load(fp)
            self.set_state(state)
        except FileNotFoundError:
            print(f"Error: The file '{filename}' does not exist.")

    def save_settings(self):
        state = self.get_state()
        filename, _ = QFileDialog.getSaveFileName(self, 'Save file', '', 'VR Settings (*.vr)')
        with open(filename, 'wb') as fp:
            state = pickle.dump(state, fp)

    def set_state(self, state: dict) -> None:

        setters = {
            'camera': self.camera_widget.set_state,
            'projector': self.projector_widget.set_state,
            'registration': self.registration_widget.set_state,
            'calibration': self.calibration_widget.set_state,
            'background': self.background_widget.set_state,
            'identity': self.identity_widget.set_state,
            'settings': self.settings_widget.set_state,
            'logs': self.logs_widget.set_state,
            'sequencer': self.sequencer_widget.set_state
        }

        for key, setter in setters.items():
            if key in state:
                setter(state[key])

        self.settings['main'] = state.get('main', {'recording_duration': 0, 'record': False})
        self.recording_duration.setValue(self.settings['main']['recording_duration'])

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

    def update_identity_settings(self):
        self.settings['identity'] = self.identity_widget.get_state()

    def update_settings(self):
        self.settings['settings'] = self.settings_widget.get_state()

    def update_logs(self):
        self.settings['logs'] = self.logs_widget.get_state()

    def update_sequencer_settings(self):
        self.settings['sequencer'] = self.sequencer_widget.get_state()

    def update_main_settings(self):
        self.settings['main']['recording_duration'] = self.recording_duration.value()

    def refresh_settings(self):
        self.update_camera_settings()
        self.update_projector_settings()
        self.update_registration_settings()
        self.update_calibration_settings()
        self.update_background_settings()
        self.update_identity_settings()
        self.update_settings()
        self.update_logs()
        self.update_sequencer_settings()
        self.update_main_settings()
    
    def registration_callback(self):
        self.camera_controller.set_preview(False)
        #self.projector_controller.set_checker(False)

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
        #self.projector_controller.set_checker(False)

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
        #self.projector_controller.set_checker(False)

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

        # update background widget
        image = np.load(self.settings['background']['background_file'])
        self.background_widget.set_image(image)
        self.sequencer_widget.set_background_image(image)
        self.identity_widget.set_image(image)

    def get_pix_per_mm_callback(self):
        self.camera_controller.set_preview(False)
        #self.projector_controller.set_checker(False)

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

    def start(self):
        self.camera_controller.set_preview(False)
        #self.projector_controller.set_checker(False)

        pprint.pprint(self.settings)
        filename = self.settings['settings']['prefix'] + '.metadata'
        with open(filename,'w') as fp:
            pprint.pprint(self.settings, fp) 

        if self.open_loop_button.isChecked():
            self.dag, self.worker_logger, self.queue_logger = open_loop(self.settings)

        elif self.video_recording_button.isChecked():
            self.dag, self.worker_logger, self.queue_logger = video_recording(self.settings)

        elif self.tracking_button.isChecked():
            self.dag, self.worker_logger, self.queue_logger = tracking(self.settings)

        elif self.close_loop_button.isChecked():
            self.dag, self.worker_logger, self.queue_logger = closed_loop(self.settings)
        
        else:
            raise RuntimeError()

        self.p_worker_logger = Process(target=self.worker_logger.run)
        self.p_queue_logger = Process(target=self.queue_logger.run)
        self.p_worker_logger.start()
        self.p_queue_logger.start()
        self.dag.start()

    def stop(self):

        if self.dag is not None:
            self.dag.stop()
            self.worker_logger.stop()
            self.queue_logger.stop()
            self.p_worker_logger.join()
            self.p_queue_logger.join()

    def preview(self):
        self.settings['main']['record'] = False
        self.start()
        
    def record(self):
        # TODO make sleep interruptible by stop ? 

        self.settings['main']['record'] = True
        self.start() 
        time.sleep(self.settings['main']['recording_duration']) 
        self.stop()

    def closeEvent(self, event):
        # close all widgets. Ensures that cleanup logic defined in closeEvent 
        # is executed
        self.camera_widget.close()
        self.projector_widget.close()
        self.registration_widget.close()
        self.calibration_widget.close()
        self.background_widget.close()
        self.identity_widget.close()
        self.sequencer_widget.close()
        self.settings_widget.close()
        self.logs_widget.close()