# This is apparently very important to set. Otherwise OpenCV warpAffine
# takes way to much time when run in a separate process
import os
os.environ["OMP_NUM_THREADS"] = "1"

from camera_tools import Camera
from tracker import (
    GridAssignment, MultiFishTracker, MultiFishTracker_CPU, MultiFishOverlay, MultiFishOverlay_opencv, MultiFishTracking,
    AnimalTracker_CPU, AnimalOverlay_opencv, AnimalTrackerParamTracking, AnimalTrackerParamOverlay, 
    BodyTracker_CPU, BodyOverlay_opencv, BodyTrackerParamTracking, BodyTrackerParamOverlay,  
)
from multiprocessing_logger import Logger
from ipc_tools import MonitoredQueue, ObjectRingBuffer2, QueueMP
from video_tools import BackgroundSubtractor, BackroundImage
from image_tools import im2single, im2gray
from dagline import WorkerNode, receive_strategy, send_strategy, ProcessingDAG
from ZebVR.stimulus import VisualStimWorker, Phototaxis, OMR, OKR, PreyCapture, Looming, DotMotion

import numpy as np
from numpy.typing import NDArray
import time
from typing import Callable, Any, Dict, Tuple, Optional
import cv2
import json

from dagline import plot_logs as plot_worker_logs
from ipc_tools import plot_logs as plot_queue_logs

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QPushButton, QGroupBox
from qt_widgets import LabeledEditLine, LabeledSpinBox, LabeledDoubleSpinBox, LabeledSliderDoubleSpinBox, NDarray_to_QPixmap


from ZebVR.config import (
    CALIBRATION_FILE, CAM_WIDTH, CAM_HEIGHT,
    CAM_EXPOSURE_MS, CAM_GAIN, CAM_FPS,
    CAM_OFFSETX, CAM_OFFSETY, 
    PROJ_WIDTH, PROJ_HEIGHT, PROJ_POS, PROJ_FPS,
    PIXEL_SCALING, BACKGROUND_FILE, IMAGE_FOLDER,
    POLARITY, ANIMAL_TRACKING_PARAM,
    BODY_TRACKING_PARAM, FOREGROUND_COLOR, 
    BACKGROUND_COLOR, CAMERA_CONSTRUCTOR
)

class MainGui(QWidget):
    
    def __init__(self, workers: Dict, queues: Dict, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.dag = None
        self.workers = workers
        self.queues = queues
        self.create_dag()
        self.create_components()
        self.layout_components()

    def create_dag(self):

        #TODO maybe reset queues to make sure they are empty and monitored queues timings are reset

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
                receiver=self.workers['visual_stim'], 
                queue=self.queues['tracker_to_stim'], 
                name='stimulus'
            )
            self.dag.connect_data(
                sender=self.workers[f'tracker_{i}'], 
                receiver=self.workers['overlay'], 
                queue=self.queues['tracker_to_overlay'], 
                name='overlay'
            )

        self.dag.connect_data(
            sender=self.workers['overlay'], 
            receiver=self.workers['display'], 
            queue=self.queues['overlay_to_display'], 
            name='disp'
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
        
        for i in range(N_TRACKER_WORKERS):
            self.dag.connect_metadata(
                sender=self.workers['tracker_gui'], 
                receiver=self.workers[f'tracker_{i}'], 
                queue=self.queues[f'tracker_control_to_tracker_{i}'], 
                name=f'tracker_control_{i}'
            )

    def create_components(self):
        
        # calibration
        self.registration_button = QPushButton()
        self.registration_button.setText('registration')
        self.registration_button.clicked.connect(self.registration)

        self.check_registration_button = QPushButton()
        self.check_registration_button.setText('check registration')
        self.check_registration_button.clicked.connect(self.check_registration)

        self.pixel_size_button = QPushButton()
        self.pixel_size_button.setText('get pix/mm')
        self.pixel_size_button.clicked.connect(self.get_pix_per_mm)

        self.check_pixel_size_button = QPushButton()
        self.check_pixel_size_button.setText('check pix/mm')
        self.check_pixel_size_button.clicked.connect(self.check_pix_per_mm)

        self.label_method = QLabel()
        self.label_method.setText('Background type:')
        self.background_method = QComboBox()
        self.background_method.addItem('static')
        self.background_method.addItem('inpaint')

        self.background_button = QPushButton()
        self.background_button.setText('background')
        self.background_button.clicked.connect(self.background)

        # experiment
        self.fish_id = LabeledSpinBox()
        self.fish_id.setText('Fish ID:')
        self.fish_id.setValue(0)
        self.fish_id.valueChanged.connect(self.experiment_data)

        self.dpf = LabeledSpinBox()
        self.dpf.setText('Fish age (dpf):')
        self.dpf.setValue(7)
        self.dpf.valueChanged.connect(self.experiment_data)

        self.duration = LabeledSpinBox()
        self.duration.setText('rec. duration (s)')
        self.duration.setValue(60)
        self.duration.valueChanged.connect(self.experiment_data)

        self.filename = LabeledEditLine()
        self.filename.setLabel('result file:')

        self.label_stimulus = QLabel()
        self.label_stimulus.setText('Visual simulus:')
        
        # TODO maybe I need to reconstzruct the DAG each time
        self.stimulus = QComboBox()
        self.stimulus.addItem('Phototaxis')
        self.stimulus.addItem('OMR')
        self.stimulus.addItem('OKR')
        self.stimulus.addItem('Looming')
        self.stimulus.addItem('PreyCapture')
        self.stimulus.currentIndexChanged.connect(self.stimulus_changed)
        
        self.start_button = QPushButton()
        self.start_button.setText('start')
        self.start_button.clicked.connect(self.start)

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
        layout.addStretch()
        layout.addWidget(self.pixel_size_button)
        layout.addWidget(self.check_pixel_size_button)
        layout.addWidget(self.registration_button)
        layout.addWidget(self.check_registration_button)
        layout.addWidget(self.label_method)
        layout.addWidget(self.background_method)
        layout.addWidget(self.background_button)
        layout.addWidget(self.fish_id)
        layout.addWidget(self.dpf)
        layout.addWidget(self.duration)
        layout.addWidget(self.filename)
        layout.addWidget(self.label_stimulus)
        layout.addWidget(self.stimulus)
        layout.addLayout(controls)
        layout.addStretch()

    def experiment_data(self):
        pass

    def registration(self):
        pass

    def check_registration(self):
        pass

    def background(self):
        pass

    def get_pix_per_mm(self):
        pass

    def check_pix_per_mm(self):
        pass
    
    def stimulus_changed(self):
        pass
    
    def start(self):
        self.dag.start()

    def stop(self):
        self.dag.stop()
        print('cam to background', self.queues['camera_to_background'].get_average_freq(), self.queues['camera_to_background'].queue.num_lost_item.value)
        if RECORD_VIDEO:
            print('cam to image saver', self.queues['camera_to_video_recorder'].get_average_freq(), self.queues['camera_to_video_recorder'].queue.num_lost_item.value)
        print('background to trackers', self.queues['background_to_tracker'].get_average_freq(), self.queues['background_to_tracker'].queue.num_lost_item.value)
        print('trackers to visual stim', self.queues['tracker_to_stim'].get_average_freq(), self.queues['tracker_to_stim'].queue.num_lost_item.value)
        print('trackers to overlay', self.queues['tracker_to_overlay'].get_average_freq(), self.queues['tracker_to_overlay'].queue.num_lost_item.value)
        print('overlay to display', self.queues['overlay_to_display'].get_average_freq(), self.queues['overlay_to_display'].queue.num_lost_item.value)

    def record(self):
        self.start()
        time.sleep(self.duration.value)
        self.stop()

class TrackerGui(WorkerNode):

    def initialize(self) -> None:
        super().initialize()
        
        self.updated = False
        self.app = QApplication([])
        self.window = QWidget()
        self.declare_components()
        self.layout_components()
        self.window.show()

    def declare_components(self):
        self.animal_pix_per_mm = LabeledDoubleSpinBox()
        self.animal_pix_per_mm.setText('pix/mm')
        self.animal_pix_per_mm.setRange(0,200)
        self.animal_pix_per_mm.setValue(ANIMAL_TRACKING_PARAM['pix_per_mm'])

        self.animal_target_pix_per_mm = LabeledDoubleSpinBox()
        self.animal_target_pix_per_mm.setText('target pix/mm')
        self.animal_target_pix_per_mm.setRange(0,200)
        self.animal_target_pix_per_mm.setValue(ANIMAL_TRACKING_PARAM['target_pix_per_mm'])

        self.animal_intensity = LabeledDoubleSpinBox()
        self.animal_intensity.setText('intensity')
        self.animal_intensity.setRange(0,1)
        self.animal_intensity.setValue(ANIMAL_TRACKING_PARAM['animal_intensity'])

        self.animal_brightness = LabeledDoubleSpinBox()
        self.animal_brightness.setText('brightness')
        self.animal_brightness.setRange(-1,1)
        self.animal_brightness.setValue(ANIMAL_TRACKING_PARAM['animal_brightness'])

        self.animal_gamma = LabeledDoubleSpinBox()
        self.animal_gamma.setText('gamma')
        self.animal_gamma.setRange(-10,10)
        self.animal_gamma.setValue(ANIMAL_TRACKING_PARAM['animal_gamma'])

        self.animal_contrast = LabeledDoubleSpinBox()
        self.animal_contrast.setText('contrast')
        self.animal_contrast.setRange(-10,10)
        self.animal_contrast.setValue(ANIMAL_TRACKING_PARAM['animal_contrast'])
        
        self.animal_min_size_mm = LabeledDoubleSpinBox()
        self.animal_min_size_mm.setText('min area (mm2)')
        self.animal_min_size_mm.setRange(0,1_000)
        self.animal_min_size_mm.setValue(ANIMAL_TRACKING_PARAM['min_animal_size_mm'])

        self.animal_max_size_mm = LabeledDoubleSpinBox()
        self.animal_max_size_mm.setText('max area (mm2)')
        self.animal_max_size_mm.setRange(0,1_000)
        self.animal_max_size_mm.setValue(ANIMAL_TRACKING_PARAM['max_animal_size_mm'])

        self.animal_min_length_mm = LabeledDoubleSpinBox()
        self.animal_min_length_mm.setText('min öength (mm)')
        self.animal_min_length_mm.setRange(0,1_000)
        self.animal_min_length_mm.setValue(ANIMAL_TRACKING_PARAM['min_animal_length_mm'])
        
        self.animal_max_length_mm = LabeledDoubleSpinBox()
        self.animal_max_length_mm.setText('max length (mm)')
        self.animal_max_length_mm.setRange(0,1_000)
        self.animal_max_length_mm.setValue(ANIMAL_TRACKING_PARAM['max_animal_length_mm'])

        self.animal_min_width_mm = LabeledDoubleSpinBox()
        self.animal_min_width_mm.setText('min width (mm)')
        self.animal_min_width_mm.setRange(0,1_000)
        self.animal_min_width_mm.setValue(ANIMAL_TRACKING_PARAM['min_animal_width_mm'])

        self.animal_max_width_mm = LabeledDoubleSpinBox()
        self.animal_max_width_mm.setText('max width (mm)')
        self.animal_max_width_mm.setRange(0,1_000)
        self.animal_max_width_mm.setValue(ANIMAL_TRACKING_PARAM['max_animal_width_mm'])
        
        self.animal_blur_sz_mm = LabeledDoubleSpinBox()
        self.animal_blur_sz_mm.setText('blur size (mm)')
        self.animal_blur_sz_mm.setRange(0,100)
        self.animal_blur_sz_mm.setSingleStep(1/ANIMAL_TRACKING_PARAM['target_pix_per_mm'])
        self.animal_blur_sz_mm.setValue(ANIMAL_TRACKING_PARAM['blur_sz_mm'])

        self.animal_median_filter_sz_mm = LabeledDoubleSpinBox()
        self.animal_median_filter_sz_mm.setText('medfilt size (mm)')
        self.animal_median_filter_sz_mm.setRange(0,100)
        self.animal_median_filter_sz_mm.setSingleStep(1/ANIMAL_TRACKING_PARAM['target_pix_per_mm'])
        self.animal_median_filter_sz_mm.setValue(ANIMAL_TRACKING_PARAM['median_filter_sz_mm'])
        
        self.body_pix_per_mm = LabeledDoubleSpinBox()
        self.body_pix_per_mm.setText('pix/mm')
        self.body_pix_per_mm.setRange(0,200)
        self.body_pix_per_mm.setValue(BODY_TRACKING_PARAM['pix_per_mm'])

        self.body_target_pix_per_mm = LabeledDoubleSpinBox()
        self.body_target_pix_per_mm.setText('target pix/mm')
        self.body_target_pix_per_mm.setRange(0,200)
        self.body_target_pix_per_mm.setValue(BODY_TRACKING_PARAM['target_pix_per_mm'])
        
        self.body_intensity = LabeledDoubleSpinBox()
        self.body_intensity.setText('intensity')
        self.body_intensity.setRange(0,1)
        self.body_intensity.setValue(BODY_TRACKING_PARAM['body_intensity'])
        
        self.body_brightness = LabeledDoubleSpinBox()
        self.body_brightness.setText('brightness')
        self.body_brightness.setRange(-1,1)
        self.body_brightness.setValue(BODY_TRACKING_PARAM['body_brightness'])
        
        self.body_gamma = LabeledDoubleSpinBox()
        self.body_gamma.setText('gamma')
        self.body_gamma.setRange(-10,10)
        self.body_gamma.setValue(BODY_TRACKING_PARAM['body_gamma'])
        
        self.body_contrast = LabeledDoubleSpinBox()
        self.body_contrast.setText('contrast')
        self.body_contrast.setRange(-10,10)
        self.body_contrast.setValue(BODY_TRACKING_PARAM['body_contrast'])
        
        self.body_min_size_mm = LabeledDoubleSpinBox()
        self.body_min_size_mm.setText('min area (mm2)')
        self.body_min_size_mm.setRange(0,1_000)
        self.body_min_size_mm.setValue(BODY_TRACKING_PARAM['min_body_size_mm'])
        
        self.body_max_size_mm = LabeledDoubleSpinBox()
        self.body_max_size_mm.setText('max area (mm2)')
        self.body_max_size_mm.setRange(0,1_000)
        self.body_max_size_mm.setValue(BODY_TRACKING_PARAM['max_body_size_mm'])
        
        self.body_min_length_mm = LabeledDoubleSpinBox()
        self.body_min_length_mm.setText('min length (mm)')
        self.body_min_length_mm.setRange(0,1_000)
        self.body_min_length_mm.setValue(BODY_TRACKING_PARAM['min_body_length_mm'])
        
        self.body_max_length_mm = LabeledDoubleSpinBox()
        self.body_max_length_mm.setText('max length (mm)')
        self.body_max_length_mm.setRange(0,1_000)
        self.body_max_length_mm.setValue(BODY_TRACKING_PARAM['max_body_length_mm'])
        
        self.body_min_width_mm = LabeledDoubleSpinBox()
        self.body_min_width_mm.setText('min width (mm)')
        self.body_min_width_mm.setRange(0,1_000)
        self.body_min_width_mm.setValue(BODY_TRACKING_PARAM['min_body_width_mm'])
        
        self.body_max_width_mm = LabeledDoubleSpinBox()
        self.body_max_width_mm.setText('max width (mm)')
        self.body_max_width_mm.setRange(0,1_000)
        self.body_max_width_mm.setValue(BODY_TRACKING_PARAM['max_body_width_mm'])
        
        self.body_blur_sz_mm = LabeledDoubleSpinBox()
        self.body_blur_sz_mm.setText('blur size (mm)')
        self.body_blur_sz_mm.setRange(0,100)
        self.body_blur_sz_mm.setSingleStep(1/BODY_TRACKING_PARAM['target_pix_per_mm'])
        self.body_blur_sz_mm.setValue(BODY_TRACKING_PARAM['blur_sz_mm'])
        
        self.body_median_filter_sz_mm = LabeledDoubleSpinBox()
        self.body_median_filter_sz_mm.setText('medfilt size (mm)')
        self.body_median_filter_sz_mm.setRange(0,100)
        self.body_median_filter_sz_mm.setSingleStep(1/BODY_TRACKING_PARAM['target_pix_per_mm'])
        self.body_median_filter_sz_mm.setValue(BODY_TRACKING_PARAM['median_filter_sz_mm'])

    def layout_components(self):
        animal = QVBoxLayout()
        animal.addStretch()
        animal.addWidget(QLabel('animal'))
        animal.addWidget(self.animal_pix_per_mm)
        animal.addWidget(self.animal_target_pix_per_mm)
        animal.addWidget(self.animal_intensity)
        animal.addWidget(self.animal_brightness)
        animal.addWidget(self.animal_gamma)
        animal.addWidget(self.animal_contrast)
        animal.addWidget(self.animal_min_size_mm)
        animal.addWidget(self.animal_max_size_mm)
        animal.addWidget(self.animal_min_length_mm)
        animal.addWidget(self.animal_max_length_mm)
        animal.addWidget(self.animal_min_width_mm)
        animal.addWidget(self.animal_max_width_mm)
        animal.addWidget(self.animal_blur_sz_mm)
        animal.addWidget(self.animal_median_filter_sz_mm)
        animal.addStretch()

        body = QVBoxLayout()
        body.addStretch()
        body.addWidget(QLabel('body'))
        body.addWidget(self.body_pix_per_mm)
        body.addWidget(self.body_target_pix_per_mm)
        body.addWidget(self.body_intensity)
        body.addWidget(self.body_brightness)
        body.addWidget(self.body_gamma)
        body.addWidget(self.body_contrast)
        body.addWidget(self.body_min_size_mm)
        body.addWidget(self.body_max_size_mm)
        body.addWidget(self.body_min_length_mm)
        body.addWidget(self.body_max_length_mm)
        body.addWidget(self.body_min_width_mm)
        body.addWidget(self.body_max_width_mm)
        body.addWidget(self.body_blur_sz_mm)
        body.addWidget(self.body_median_filter_sz_mm)
        body.addStretch()

        final = QHBoxLayout(self.window)
        final.addLayout(animal)
        final.addLayout(body)

    def on_change(self):
        self.updated = True

    def process_data(self, data: None) -> NDArray:
        self.app.processEvents()

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        # send tracking controls
        if self.updated:
            self.updated = False
            res = {}
            for i in range(N_TRACKER_WORKERS):
                res[f'tracker_control_{i}'] = {}
                res[f'tracker_control_{i}']['animal_tracking'] = {}
                res[f'tracker_control_{i}']['body_tracking'] = {}
                res[f'tracker_control_{i}']['animal_tracking']['pix_per_mm']=self.animal_pix_per_mm.value()
                res[f'tracker_control_{i}']['animal_tracking']['target_pix_per_mm']=self.animal_target_pix_per_mm.value()
                res[f'tracker_control_{i}']['animal_tracking']['animal_intensity']=self.animal_intensity.value()
                res[f'tracker_control_{i}']['animal_tracking']['animal_brightness']=self.animal_brightness.value()
                res[f'tracker_control_{i}']['animal_tracking']['animal_gamma']=self.animal_gamma.value()
                res[f'tracker_control_{i}']['animal_tracking']['animal_contrast']=self.animal_contrast.value()
                res[f'tracker_control_{i}']['animal_tracking']['min_animal_size_mm']=self.animal_min_size_mm.value()
                res[f'tracker_control_{i}']['animal_tracking']['max_animal_size_mm']=self.animal_max_size_mm.value()
                res[f'tracker_control_{i}']['animal_tracking']['min_animal_length_mm']=self.animal_min_length_mm.value()
                res[f'tracker_control_{i}']['animal_tracking']['max_animal_length_mm']=self.animal_max_length_mm.value()
                res[f'tracker_control_{i}']['animal_tracking']['min_animal_width_mm']=self.animal_min_width_mm.value()
                res[f'tracker_control_{i}']['animal_tracking']['max_animal_width_mm']=self.animal_max_width_mm.value()
                res[f'tracker_control_{i}']['animal_tracking']['blur_sz_mm']=self.animal_blur_sz_mm.value()
                res[f'tracker_control_{i}']['animal_tracking']['median_filter_sz_mm']=self.animal_median_filter_sz_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['pix_per_mm']=self.body_pix_per_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['target_pix_per_mm']=self.body_target_pix_per_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['body_intensity']=self.body_intensity.value()
                res[f'tracker_control_{i}']['body_tracking']['body_brightness']=self.body_brightness.value()
                res[f'tracker_control_{i}']['body_tracking']['body_gamma']=self.body_gamma.value()
                res[f'tracker_control_{i}']['body_tracking']['body_contrast']=self.body_contrast.value()
                res[f'tracker_control_{i}']['body_tracking']['min_body_size_mm']=self.body_max_size_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['max_body_size_mm']=self.body_min_size_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['min_body_length_mm']=self.body_max_length_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['max_body_length_mm']=self.body_min_length_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['min_body_width_mm']=self.body_max_width_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['max_body_width_mm']=self.body_min_width_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['blur_sz_mm']=self.body_blur_sz_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['median_filter_sz_mm']=self.body_median_filter_sz_mm.value()
            return res

class CameraGui(WorkerNode):

    def initialize(self) -> None:
        super().initialize()
        
        self.updated = False
        self.app = QApplication([])
        self.window = QWidget()
        self.controls = [
            'framerate', 
            'exposure', 
            'gain', 
        ]
        self.declare_components()
        self.layout_components()
        self.window.show()

    def declare_components(self):

        # controls 
        for c in self.controls:
            self.create_spinbox(c)

    def create_spinbox(self, attr: str):
        '''
        Creates spinbox with correct label, value, range and increment
        as specified by the camera object. Connects to relevant
        callback.
        WARNING This is compact but a bit terse and introduces dependencies
        in the code. 
        '''
        if attr in ['framerate', 'exposure', 'gain']:
            setattr(self, attr + '_spinbox', LabeledSliderDoubleSpinBox())
        else:
            setattr(self, attr + '_spinbox', LabeledDoubleSpinBox())
        spinbox = getattr(self, attr + '_spinbox')
        spinbox.setText(attr)
        spinbox.setRange(0,100_000)
        spinbox.setSingleStep(1)
        spinbox.setValue(0)
        spinbox.valueChanged.connect(self.on_change)

    def layout_components(self):

        layout_controls = QVBoxLayout(self.window)
        layout_controls.addStretch()
        layout_controls.addWidget(self.exposure_spinbox)
        layout_controls.addWidget(self.gain_spinbox)
        layout_controls.addWidget(self.framerate_spinbox)
        layout_controls.addStretch()

    def on_change(self):
        self.updated = True

    def process_data(self, data: None) -> NDArray:
        self.app.processEvents()

    def block_signals(self, block):
        for widget in self.window.findChildren(QWidget):
            widget.blockSignals(block)

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        # receive cam inof
        info = metadata['camera_info']
        if info is not None: 
            self.block_signals(True)
            for c in self.controls:
                spinbox = getattr(self, c + '_spinbox')
                spinbox.setValue(info[c]['value'])
                spinbox.setRange(info[c]['min'], info[c]['max'])
                spinbox.setSingleStep(info[c]['increment'])
            self.block_signals(False)

        # send only one message when things are changed
        if self.updated:
            res = {}
            res['camera_control'] = {}
            for c in self.controls:
                spinbox = getattr(self, c + '_spinbox')
                res['camera_control'][c] = spinbox.value()
            self.updated = False
            return res       
        else:
            return None
        
class CameraWorker(WorkerNode):

    def __init__(
            self, 
            camera_constructor: Callable[[Camera], None], 
            exposure: float,
            gain: float,
            framerate: float,
            height: int,
            width: int,
            offsetx: int,
            offsety: int,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.camera_constructor = camera_constructor
        self.exposure = exposure
        self.gain = gain
        self.framerate = framerate
        self.height = height
        self.width = width
        self.offsetx = offsetx
        self.offsety = offsety
        self.updated = False
    
    def initialize(self) -> None:
        super().initialize()
        self.cam = self.camera_constructor()
        self.cam.set_exposure(self.exposure)
        self.cam.set_gain(self.gain)
        self.cam.set_framerate(self.framerate)
        self.cam.set_height(self.height)
        self.cam.set_width(self.width)
        self.cam.set_offsetX(self.offsetx)
        self.cam.set_offsetY(self.offsety)
        self.cam.start_acquisition()
        self.updated = True

    def cleanup(self) -> None:
        super().cleanup()
        self.cam.stop_acquisition()
    
    def process_data(self, data: None): 
        frame = self.cam.get_frame()
        if frame:
            img = im2gray(frame.image)
            res = {}
            res['background_subtraction'] = (frame.index, time.perf_counter_ns(), img)
            res['image_saver'] = (frame.index, time.perf_counter_ns(), img)
            return res
        
    def process_metadata(self, metadata) -> Any:
        # receive
        control = metadata['camera_control']
        if control is not None: 
            self.cam.stop_acquisition()
            self.cam.set_exposure(control['exposure'])
            self.cam.set_gain(control['gain'])
            self.cam.set_framerate(control['framerate'])
            self.cam.start_acquisition()
            self.updated = True
        
        # send
        # if camera settings were updated, send info
        if self.updated:
            self.updated = False
            # TODO make sure all cameras support these functions and reply something coherent
            try:
                res = {}
                res['camera_info'] = {}
                res['camera_info']['exposure'] = {}
                res['camera_info']['gain'] = {}
                res['camera_info']['framerate'] = {}
                res['camera_info']['exposure']['value'] = self.cam.get_exposure()
                res['camera_info']['exposure']['min'], res['camera_info']['exposure']['max'] = self.cam.get_exposure_range()
                res['camera_info']['exposure']['increment'] = self.cam.get_exposure_increment()
                res['camera_info']['gain']['value'] = self.cam.get_gain()
                res['camera_info']['gain']['min'], res['camera_info']['gain']['max'] = self.cam.get_gain_range()
                res['camera_info']['gain']['increment'] = self.cam.get_gain_increment()
                res['camera_info']['framerate']['value'] = self.cam.get_framerate()
                res['camera_info']['framerate']['min'], res['camera_info']['framerate']['max'] = self.cam.get_framerate_range()
                res['camera_info']['framerate']['increment'] = self.cam.get_framerate_increment()
                return res
            except:
                pass
            
class BackgroundSubWorker(WorkerNode):

    def __init__(self, sub: BackgroundSubtractor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sub = sub

    def initialize(self) -> None:
        super().initialize()
        self.sub.initialize()

    def process_data(self, data):
        if data is not None:
            index, timestamp, image = data
            res = self.sub.subtract_background(image)
            return (index, timestamp, res)

    def process_metadata(self, metadata) -> Any:
        pass

class TrackerWorker(WorkerNode):
    
    def __init__(self, tracker: MultiFishTracker, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tracker = tracker

    def initialize(self) -> None:
        super().initialize()

        # try to trigger numba compilation during init phase (doesn't work right now)
        # self.tracker.tail.track(np.zeros((100,100),dtype=np.float32), centroid=np.array([0,0]))

    def process_data(self, data: NDArray) -> Dict:
        try:
            index, timestamp, image = data
            tracking = self.tracker.track(image)
            res = {}
            k = tracking.animals.identities[0]
            res['stimulus'] = (index, timestamp, tracking.animals.centroids[k,:], tracking.body[k].heading[:,1])
            res['overlay'] = (index, timestamp, tracking)
            return res
        except:
            return None  
        
    def process_metadata(self, metadata) -> Any:
        # reveive tracker settings and update tracker
        for i in range(N_TRACKER_WORKERS):
            control = metadata[f'tracker_control_{i}']
            if control is not None: 
                self.tracker = MultiFishTracker_CPU(
                    max_num_animals=1,
                    accumulator=None, 
                    export_fullres_image=True,
                    downsample_fullres_export=0.25,
                    animal=AnimalTracker_CPU(
                        assignment=GridAssignment(LUT=np.zeros((CAM_HEIGHT,CAM_WIDTH), dtype=np.int_)), 
                        tracking_param=AnimalTrackerParamTracking(**control['animal_tracking'])
                    ),
                    body=BodyTracker_CPU(tracking_param=BodyTrackerParamTracking(**control['body_tracking'])),
                    eyes=None,
                    tail=None
                )


class OverlayWorker(WorkerNode):

    def __init__(self, overlay: MultiFishOverlay, fps: int = 30, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.overlay = overlay
        self.fps = fps
        self.prev_time = 0

    def process_data(self, data: Any) -> Dict:
        if data is not None:
            index, timestamp, tracking = data
            if time.monotonic() - self.prev_time > 1/self.fps:
                if tracking.animals.identities is not None:
                    overlay = self.overlay.overlay(tracking.image, tracking)
                    self.prev_time = time.monotonic()
                    return (index, timestamp, overlay)

    def process_metadata(self, metadata) -> Any:
        pass

class Display(WorkerNode):

    def __init__(self, fps: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fps = fps
        self.prev_time = 0

    def initialize(self) -> None:
        super().initialize()
        cv2.namedWindow('display')
    
    def cleanup(self) -> None:
        super().cleanup()
        cv2.destroyAllWindows()

    def process_data(self, data: NDArray) -> None:
        if data is not None:
            index, timestamp, image = data
            if time.monotonic() - self.prev_time > 1/self.fps:
                cv2.imshow('display', image) # NOT data[0]
                cv2.waitKey(1)
                self.prev_time = time.monotonic()

    def process_metadata(self, metadata) -> Any:
        pass

class ImageSaver(WorkerNode):

    def __init__(self, folder: str, zero_padding: int = 8, compress: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.folder = folder
        self.zero_padding = zero_padding
        self.compress = compress

    def initialize(self) -> None:
        super().initialize()
        if not os.path.exists(self.folder):
            os.mkdir(self.folder)

    def process_data(self, data: NDArray) -> None:
        if data is not None:
            index, timestamp, image = data
            image_resized = cv2.resize(image,None,None,0.25,0.25,cv2.INTER_NEAREST)
            metadata = np.array( 
                (index, timestamp), 
                dtype = np.dtype([('index',np.int64), ('timestamp',np.float32)]) 
            )
            filename = os.path.join(self.folder, f'{index:0{self.zero_padding}}')
            if self.compress:
                np.savez_compressed(filename, image=image_resized, metadata=metadata)
            else:
                np.savez(filename, image=image_resized, metadata=metadata)

    def process_metadata(self, metadata) -> Any:
        pass
    
if __name__ == "__main__":

    LOGFILE_WORKERS = 'workers.log'
    LOGFILE_QUEUES = 'queues.log'

    # TODO profile with just one worker, otherwise lot of time waiting for data
    N_BACKGROUND_WORKERS = 1
    N_TRACKER_WORKERS = 1
    BACKGROUND_GPU = False
    T_REFRESH = 1e-4

    RECORD_VIDEO = False
    DARKLEFT = True

    with open(CALIBRATION_FILE, 'r') as f:
        calibration = json.load(f)

    o = MultiFishOverlay_opencv(
        AnimalOverlay_opencv(AnimalTrackerParamOverlay()),
        BodyOverlay_opencv(BodyTrackerParamOverlay()),
        None,
        None,
    )
    
    t = MultiFishTracker_CPU(
        max_num_animals=1,
        accumulator=None, 
        export_fullres_image=True,
        downsample_fullres_export=0.25,
        animal=AnimalTracker_CPU(
            assignment=GridAssignment(LUT=np.zeros((CAM_HEIGHT,CAM_WIDTH), dtype=np.int_)), 
            tracking_param=AnimalTrackerParamTracking(**ANIMAL_TRACKING_PARAM)
        ),
        body=BodyTracker_CPU(tracking_param=BodyTrackerParamTracking(**BODY_TRACKING_PARAM)),
        eyes=None,
        tail=None
    )

    worker_logger = Logger(LOGFILE_WORKERS, Logger.INFO)
    queue_logger = Logger(LOGFILE_QUEUES, Logger.INFO)

    b = BackroundImage(
        image_file_name = BACKGROUND_FILE,
        polarity = POLARITY,
        use_gpu = BACKGROUND_GPU
    )
    
    ptx = Phototaxis(
        window_size=(PROJ_WIDTH, PROJ_HEIGHT),
        window_position=PROJ_POS,
        foreground_color=FOREGROUND_COLOR,
        background_color=BACKGROUND_COLOR,
        window_decoration=False,
        transformation_matrix=np.array(calibration['cam_to_proj'], dtype=np.float32),
        refresh_rate=PROJ_FPS,
        vsync=True,
        pixel_scaling=PIXEL_SCALING,
        darkleft = DARKLEFT
    )

    omr = OMR(
        window_size=(PROJ_WIDTH, PROJ_HEIGHT),
        window_position=PROJ_POS,
        foreground_color=FOREGROUND_COLOR,
        background_color=BACKGROUND_COLOR,        
        window_decoration=False,
        transformation_matrix=np.array(calibration['cam_to_proj'], dtype=np.float32),
        refresh_rate=PROJ_FPS,
        vsync=True,
        pixel_scaling=PIXEL_SCALING
    )

    okr = OKR(
        window_size=(PROJ_WIDTH, PROJ_HEIGHT),
        window_position=PROJ_POS,
        foreground_color=FOREGROUND_COLOR,
        background_color=BACKGROUND_COLOR,        
        window_decoration=False,
        transformation_matrix=np.array(calibration['cam_to_proj'], dtype=np.float32),
        refresh_rate=PROJ_FPS,
        vsync=True,
        pixel_scaling=PIXEL_SCALING
    )

    looming = Looming(
        window_size=(PROJ_WIDTH, PROJ_HEIGHT),
        window_position=PROJ_POS,
        foreground_color=FOREGROUND_COLOR,
        background_color=BACKGROUND_COLOR,        
        window_decoration=False,
        transformation_matrix=np.array(calibration['cam_to_proj'], dtype=np.float32),
        refresh_rate=PROJ_FPS,
        vsync=True,
        pixel_scaling=PIXEL_SCALING
    )

    preycapture = PreyCapture(
        window_size=(PROJ_WIDTH, PROJ_HEIGHT),
        window_position=PROJ_POS,
        foreground_color=FOREGROUND_COLOR,
        background_color=BACKGROUND_COLOR,        
        window_decoration=False,
        transformation_matrix=np.array(calibration['cam_to_proj'], dtype=np.float32),
        refresh_rate=PROJ_FPS,
        vsync=True,
        pixel_scaling=PIXEL_SCALING
    )

    cam_control = CameraGui(
        name='cam_gui',  
        logger=worker_logger, 
        logger_queues=queue_logger
    )

    tracker_control = TrackerGui(
        name='tracker_gui',  
        logger=worker_logger, 
        logger_queues=queue_logger   
    )
    
    cam = CameraWorker(
        camera_constructor = CAMERA_CONSTRUCTOR, 
        exposure = CAM_EXPOSURE_MS,
        gain = CAM_GAIN,
        framerate = CAM_FPS,
        height = CAM_HEIGHT,
        width = CAM_WIDTH,
        offsetx = CAM_OFFSETX,
        offsety = CAM_OFFSETY,
        name='camera', 
        logger=worker_logger, 
        logger_queues=queue_logger, 
        receive_data_strategy=receive_strategy.COLLECT, 
        send_data_strategy=send_strategy.BROADCAST, 
        receive_data_timeout=1.0
    )

    image_saver = ImageSaver(
        folder = IMAGE_FOLDER, 
        name='image_saver',  
        logger=worker_logger, 
        logger_queues=queue_logger, 
        receive_data_timeout=1.0
    )

    bckg = []
    for i in range(N_BACKGROUND_WORKERS):
        bckg.append(BackgroundSubWorker(b, name=f'background{i}', logger=worker_logger, logger_queues=queue_logger, receive_data_timeout=1.0, profile=False))

    trck = []
    for i in range(N_TRACKER_WORKERS):
        trck.append(TrackerWorker(t, name=f'tracker{i}', logger=worker_logger, logger_queues=queue_logger, send_data_strategy=send_strategy.BROADCAST, receive_data_timeout=1.0, profile=False))

    dis = Display(
        fps=30, 
        name='display', 
        logger=worker_logger, 
        logger_queues=queue_logger, 
        receive_data_timeout=1.0
    )

    stim = VisualStimWorker(
        stim=omr, 
        name='phototaxis', 
        logger=worker_logger, 
        logger_queues=queue_logger, 
        receive_data_timeout=1.0
    )

    oly = OverlayWorker(
        overlay=o, 
        fps=30, 
        name="overlay", 
        logger=worker_logger, 
        logger_queues=queue_logger, 
        receive_data_timeout=1.0
    )

    # ring buffer camera ------------------------------------------------------------------ 
    dt_uint8_RGB = np.dtype([
        ('index', int, (1,)),
        ('timestamp', float, (1,)), 
        ('image', np.uint8, (CAM_HEIGHT,CAM_WIDTH,3))
    ])

    dt_uint8_gray = np.dtype([
        ('index', int, (1,)),
        ('timestamp', float, (1,)), 
        ('image', np.uint8, (CAM_HEIGHT,CAM_WIDTH))
    ])

    dt_downsampled_uint8_RGB = np.dtype([
        ('index', int, (1,)),
        ('timestamp', float, (1,)), 
        ('image', np.uint8, (round(CAM_HEIGHT*t.downsample_fullres_export), round(CAM_WIDTH*t.downsample_fullres_export), 3))
    ])


    def serialize_image(buffer: NDArray, obj: Tuple[int, float, NDArray]) -> None:
        #tic = time.monotonic_ns()
        #buffer[:] = obj # this is slower, why ?
        index, timestamp, image = obj 
        buffer['index'] = index
        buffer['timestamp'] = timestamp
        buffer['image'] = image
        #print(buffer.dtype, 1e-6*(time.monotonic_ns() - tic))

    def deserialize_image(arr: NDArray) -> Tuple[int, float, NDArray]:
        index = arr['index'].item()
        timestamp = arr['timestamp'].item()
        image = arr[0]['image']
        return (index, timestamp, image)

    q_cam = MonitoredQueue(
        ObjectRingBuffer2(
            num_items = 100,
            data_type = dt_uint8_gray,
            serialize = serialize_image,
            deserialize = deserialize_image,
            logger = queue_logger,
            name = 'camera_to_background',
            t_refresh=T_REFRESH
        )
    )

    q_save_image = MonitoredQueue(
        ObjectRingBuffer2(
            num_items = 100,
            data_type = dt_uint8_gray,
            serialize = serialize_image,
            deserialize = deserialize_image,
            logger = queue_logger,
            name = 'camera_to_image_saver',
            t_refresh=T_REFRESH
        )
    )

    q_display = MonitoredQueue(
        ObjectRingBuffer2(
            num_items = 100,
            data_type = dt_downsampled_uint8_RGB,
            serialize = serialize_image,
            deserialize = deserialize_image,
            logger = queue_logger,
            name = 'overlay_to_display',
            t_refresh=T_REFRESH
        )
    )


    # ring buffer background ------------------------------------------------------------------
    # IMPORTANT: need to copy the data out of the 
    # circular buffer otherwise it can be modified after the fact
    # set copy=True
    
    dt_single_gray = np.dtype([
        ('index', int, (1,)),
        ('timestamp', float, (1,)), 
        ('image', np.float32, (CAM_HEIGHT,CAM_WIDTH))
    ])

    q_back = MonitoredQueue(
        ObjectRingBuffer2(
            num_items = 100,
            data_type = dt_single_gray,
            serialize = serialize_image,
            deserialize = deserialize_image,
            copy=False, # you probably don't need to copy if processing is fast enough
            logger = queue_logger,
            name = 'background_to_trackers',
            t_refresh=T_REFRESH
        )
    )

    # tracking ring buffer -------------------------------------------------------------------
    # get dtype and itemsize for tracker results
    tracking = t.track(np.zeros((CAM_HEIGHT,CAM_WIDTH), dtype=np.float32))
    arr_multifish = tracking.to_numpy()

    dt_tracking_multifish = np.dtype([
        ('index', int, (1,)),
        ('timestamp', float, (1,)), 
        ('tracking', arr_multifish.dtype, (1,))
    ])

    def serialize_tracking_multifish(buffer: NDArray, obj: Tuple[int, float, MultiFishTracking]) -> NDArray:
        #tic = time.monotonic_ns()
        index, timestamp, tracking = obj
        buffer['index'] = index
        buffer['timestamp'] = timestamp
        tracking.to_numpy(buffer['tracking'])
        #buffer['tracking'] = tracking.to_numpy() # maybe it should be tracking.to_numpy(array_to_copy_into) to write directly to the buffer. Rewrite function as tracking(out: Optional[NDArray] = None)
        #print(buffer.dtype, 1e-6*(time.monotonic_ns() - tic))


    def deserialize_tracking_multifish(arr: NDArray) -> Tuple[int, float, MultiFishTracking]:
        index = arr['index'].item()
        timestamp = arr['timestamp'].item()
        tracking = MultiFishTracking.from_numpy(arr[0]['tracking'][0])
        return (index, timestamp, tracking)

    # ---
    dt_tracking_body = np.dtype([
        ('index', int, (1,)),
        ('timestamp', float, (1,)), 
        ('centroid', np.float32, (1,2)),
        ('heading', np.float32, (2,))
    ])

    def serialize_tracking_body(buffer: NDArray, obj: Tuple[int, float, NDArray, NDArray]) -> NDArray:
        index, timestamp, centroid, heading = obj
        buffer['index'] = index
        buffer['timestamp'] = timestamp
        buffer['centroid'] = centroid
        buffer['heading'] = heading

    def deserialize_tracking_body(arr: NDArray) -> Tuple[int, float, NDArray, NDArray]:
        index = arr['index'].item()
        timestamp = arr['timestamp'].item()
        centroid = arr[0]['centroid']
        heading = arr[0]['heading']
        return (index, timestamp, centroid, heading)

    q_tracking = MonitoredQueue(
        ObjectRingBuffer2(
            num_items = 100,
            data_type = dt_tracking_body,
            serialize = serialize_tracking_body,
            deserialize = deserialize_tracking_body,
            logger = queue_logger,
            name = 'tracker_to_phototaxis',
            t_refresh=T_REFRESH
        )
    )

    q_overlay = MonitoredQueue(
        ObjectRingBuffer2(
            num_items = 100,
            data_type = dt_tracking_multifish,
            serialize = serialize_tracking_multifish,
            deserialize = deserialize_tracking_multifish,
            logger = queue_logger,
            name = 'tracker_to_overlay',
            t_refresh=T_REFRESH
        )
    )

    ## ----------------------------------------------------------------------

    workers = {
        'camera': cam,
        'camera_gui': cam_control,
        'video_recorder': image_saver,
        'visual_stim': stim,
        'overlay': oly,
        'display': dis,
        'tracker_gui': tracker_control
    }
    for i in range(N_TRACKER_WORKERS):
        workers[f'tracker_{i}'] = trck[i]
    for i in range(N_BACKGROUND_WORKERS):
        workers[f'background_{i}'] = bckg[i]
        
    queues = {
        'camera_to_background': q_cam,
        'camera_to_video_recorder': q_save_image,
        'background_to_tracker': q_back,
        'tracker_to_stim': q_tracking,
        'tracker_to_overlay': q_overlay,
        'overlay_to_display': q_display,
        'camera_control_to_camera': QueueMP(),
        'camera_to_camera_control': QueueMP()
    }
    for i in range(N_TRACKER_WORKERS):
        queues[f'tracker_control_to_tracker_{i}'] = QueueMP()

    app = QApplication([])
    main = MainGui(workers=workers, queues=queues)
    main.show()
    app.exec_()
