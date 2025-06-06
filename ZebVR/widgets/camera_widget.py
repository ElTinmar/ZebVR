from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLabel, 
    QPushButton, 
    QComboBox, 
    QFileDialog,
    QApplication
)
from PyQt5.QtCore import pyqtSignal, QRunnable, QThreadPool, QObject, QTimer
from PyQt5.QtGui import QImage
import numpy as np
import cv2
import os
from functools import partial
from typing import Dict, Optional, Callable
from numpy.typing import NDArray
from enum import IntEnum

from qt_widgets import LabeledDoubleSpinBox, LabeledSpinBox, NDarray_to_QPixmap
from camera_tools import (
    Camera, 
    OpenCV_Webcam, 
    OpenCV_Webcam_Gray,
    OpenCV_Webcam_InitEveryFrame, 
    MovieFileCam, 
    ZeroCam
)

class CameraModel(IntEnum):
    ZERO_GRAY = 0
    ZERO_RGB = 1
    WEBCAM = 2
    WEBCAM_GRAY = 3
    WEBCAM_REGISTRATION = 4
    XIMEA = 5
    SPINNAKER = 6
    MOVIE = 7

try:
    from camera_tools import XimeaCamera, XimeaCamera_Transport
    XIMEA_ENABLED = True
except ImportError:
    XIMEA_ENABLED = False

try:
    from camera_tools import SpinnakerCamera
    SPINNAKER_ENABLED = True
except ImportError:
    SPINNAKER_ENABLED = False

class CameraWidget(QWidget):

    source_changed = pyqtSignal(int, int, str)
    state_changed = pyqtSignal()
    preview = pyqtSignal(bool)
    PREVIEW_HEIGHT: int = 480
    REFRESH_RATE = 30

    def __init__(self,*args,**kwargs):

        super().__init__(*args, **kwargs)
        
        self.controls = [
            'width',
            'height',
            'offsetX', 
            'offsetY', 
            'framerate', 
            'exposure', 
            'gain'
        ]

        self.image = np.zeros((self.PREVIEW_HEIGHT,self.PREVIEW_HEIGHT), dtype=np.uint8)
        self.declare_components()
        self.layout_components()
        self.setWindowTitle('Camera controls')

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.set_pixmap)
        self.timer.start(1000/self.REFRESH_RATE) 

    def declare_components(self) -> None:

        self.camera_model = QComboBox()
        self.camera_model.addItems([model.name for model in CameraModel])
        self.camera_model.currentTextChanged.connect(self.on_source_change)

        self.camera_id = LabeledSpinBox()
        self.camera_id.setText('Camera ID:')
        self.camera_id.setEnabled(True)
        self.camera_id.valueChanged.connect(self.on_source_change)
        
        self.movie_load = QPushButton('Load file')
        self.movie_load.setEnabled(False)
        self.movie_load.clicked.connect(self.load_file)
    
        self.filename = QLabel('')

        # controls 
        for control in self.controls:
            if control in ['framerate','gain', 'exposure']:
                constructor = LabeledDoubleSpinBox
            elif control in ['offsetX', 'offsetY', 'height', 'width']:
                constructor = LabeledSpinBox

            setattr(self, control + '_spinbox', constructor())
            spinbox = getattr(self, control + '_spinbox')
            spinbox.setText(control)
            spinbox.setRange(0,0)
            spinbox.setSingleStep(0)
            spinbox.setValue(0)
            spinbox.setEnabled(False)
            spinbox.valueChanged.connect(self.state_changed)

        self.num_channels_label = QLabel()
        self.num_channels_label.setText('Num channels:')
        self.num_channels = QLabel()
        self.num_channels.setText('0')

        # image
        self.preview_start = QPushButton('start preview')
        self.preview_start.clicked.connect(self.start)

        self.preview_stop = QPushButton('stop preview')
        self.preview_stop.clicked.connect(self.stop)

        self.image_label = QLabel()

    def load_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "Load movie",
            "",
            "Movie file (*.avi)"
        )
        self.filename.setText(filename)
        self.on_source_change()

    def start(self):
        self.preview.emit(True)

    def stop(self):
        self.preview.emit(False)

    def set_image(self, image: NDArray):
        self.image = image

    def set_pixmap(self):
        # TODO maybe check that image is uint8
        h, w = self.image.shape[:2]
        preview_width = int(w * self.PREVIEW_HEIGHT/h)
        image_resized = cv2.resize(self.image,(preview_width, self.PREVIEW_HEIGHT), cv2.INTER_NEAREST)
        pixmap = NDarray_to_QPixmap(image_resized, format = QImage.Format_RGB888)
        self.image_label.setPixmap(pixmap)

    def layout_components(self) -> None:

        layout_buttons = QHBoxLayout()
        layout_buttons.addWidget(self.preview_start)
        layout_buttons.addWidget(self.preview_stop)

        layout_moviecam = QHBoxLayout()
        layout_moviecam.addWidget(self.movie_load)
        layout_moviecam.addWidget(self.filename)

        layout_cam = QVBoxLayout()
        layout_cam.addWidget(self.camera_id)
        layout_cam.addLayout(layout_moviecam)

        layout_channels = QHBoxLayout()
        layout_channels.addWidget(self.num_channels_label)
        layout_channels.addWidget(self.num_channels)

        layout_controls = QVBoxLayout(self)
        layout_controls.addWidget(self.camera_model)
        layout_controls.addLayout(layout_cam)

        for control in self.controls:
            spinbox = getattr(self, control + '_spinbox')
            layout_controls.addWidget(spinbox)

        layout_image = QHBoxLayout()
        layout_image.addStretch()
        layout_image.addWidget(self.image_label)
        layout_image.addStretch()

        layout_controls.addLayout(layout_channels)
        layout_controls.addLayout(layout_buttons)
        layout_controls.addStretch()
        layout_controls.addLayout(layout_image)
        layout_controls.addStretch()

    def on_source_change(self):
        model = self.camera_model.currentIndex()
        id = self.camera_id.value() 
        filename = self.filename.text()

        if model == CameraModel.MOVIE:
            self.camera_id.setEnabled(False)
            self.movie_load.setEnabled(True)
        else:
            self.camera_id.setEnabled(True)
            self.movie_load.setEnabled(False)

        self.source_changed.emit(model, id, filename)

    def block_signals(self, block):
        for widget in self.findChildren(QWidget):
            widget.blockSignals(block)

    def get_state(self) -> Dict:

        state = {}
        state['camera_model'] = self.camera_model.currentIndex()
        state['camera_index'] = self.camera_id.value()
        state['movie_file'] = self.filename.text()
        for control in self.controls:
            spinbox = getattr(self, control + '_spinbox')
            state[control + '_enabled'] = spinbox.isEnabled()
            state[control + '_min'] = spinbox.minimum()
            state[control + '_max'] = spinbox.maximum()
            state[control + '_step'] = spinbox.singleStep()
            state[control + '_value'] = spinbox.value()
        state['num_channels'] = int(self.num_channels.text())
        return state
    
    def set_state(self, state: Dict) -> None:

        setters = {
            'camera_index': self.camera_id.setValue,
            'movie_file': self.filename.setText,
            'camera_model': self.camera_model.setCurrentIndex,
            'num_channels': lambda x: self.num_channels.setText(str(x)),
        }

        for control in self.controls:
            attr = control + '_spinbox'
            spinbox = getattr(self, attr)

            setter = {
                control + '_enabled': spinbox.setEnabled,
                control + '_min': spinbox.setMinimum,
                control + '_max': spinbox.setMaximum,
                control + '_step': spinbox.setSingleStep,
                control + '_value': spinbox.setValue
            }
            
            setters.update(setter)
        
        for key, setter in setters.items():
            if key in state:
                setter(state[key])
    
    def closeEvent(self, event):
        # If widget is a children of some other widget, it needs
        # to be explicitly closed for this to happen
        self.stop()

class CameraAcquisition(QRunnable):

    def __init__(self, camera_constructor: Callable[[], Camera], widget: CameraWidget):
        super().__init__()
        self.camera_constructor = camera_constructor
        self.widget = widget
        self.keepgoing = True
        
    def stop(self):
        self.keepgoing = False
    
    def run(self):
        camera = self.camera_constructor()
        state = self.widget.get_state()
        camera.set_width(state['width_value'])
        camera.set_height(state['height_value'])
        camera.set_offsetX(state['offsetX_value'])
        camera.set_offsetY(state['offsetY_value'])
        camera.set_exposure(state['exposure_value'])
        camera.set_framerate(state['framerate_value'])
        camera.set_gain(state['gain_value'])
        camera.start_acquisition()
        while self.keepgoing:
            try:                
                frame = camera.get_frame()
                if frame['image'] is not None:
                    self.widget.set_image(frame['image'])
            except Exception as e:
                print(e)
                
        camera.stop_acquisition()

class CameraController(QObject):

    state_changed = pyqtSignal()

    def __init__(self, view: CameraWidget, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.view = view

        self.camera_constructor = None
        self.thread_pool = QThreadPool()
        self.acq = None
        self.camera_preview_started = False
        
        self.camera_model= None
        self.camera_index = None
        self.filename = None

        # connect view signals to controller methods
        self.view.source_changed.connect(self.on_source_changed)
        self.view.state_changed.connect(self.on_state_changed)
        self.view.preview.connect(self.set_preview)

        # initialize view
        self.view.on_source_change()

    def on_source_changed(self, camera_model: int, cam_ind: int, filename: str):

        self.camera_model = camera_model
        self.camera_index = cam_ind
        self.filename = filename

        if camera_model==CameraModel.ZERO_GRAY:
            self.camera_constructor = partial(ZeroCam, shape=(2048,2048), dtype=np.uint8)
        
        elif camera_model==CameraModel.ZERO_RGB:
            self.camera_constructor = partial(ZeroCam, shape=(2048,2048,3), dtype=np.uint8)

        elif camera_model==CameraModel.WEBCAM:
            self.camera_constructor = partial(OpenCV_Webcam, cam_id=cam_ind)

        elif camera_model==CameraModel.WEBCAM_GRAY:
            self.camera_constructor = partial(OpenCV_Webcam_Gray, cam_id=cam_ind)
        
        elif camera_model==CameraModel.WEBCAM_REGISTRATION:
            self.camera_constructor = partial(OpenCV_Webcam_InitEveryFrame, cam_id=cam_ind)
        
        elif camera_model==CameraModel.SPINNAKER and SPINNAKER_ENABLED:
            self.camera_constructor = partial(SpinnakerCamera, dev_id=cam_ind)

        elif camera_model==CameraModel.MOVIE and os.path.exists(filename):
            self.camera_constructor = partial(MovieFileCam, filename=filename)

        elif camera_model==CameraModel.XIMEA and XIMEA_ENABLED:
            self.camera_constructor = partial(XimeaCamera_Transport, dev_id=cam_ind)

        camera = self.camera_constructor()
        self.view.block_signals(True)
        
        try:
            self.view.set_state(self.get_camera_state(camera))
        except Exception as e:
            print(e)

        self.view.block_signals(False)

        self.state_changed.emit()

    def get_camera_state(self, camera: Camera) -> Optional[Dict]: 

        # read camera properties and set widget state accordingly
        state = {}
        
        state['camera_model'] = self.camera_model
        state['camera_index'] = self.camera_index
        state['movie_file'] = self.filename

        framerate_enabled = camera.framerate_available()
        state['framerate_enabled'] = framerate_enabled
        state['framerate_min'], state['framerate_max'] = camera.get_framerate_range() if framerate_enabled else (0,10_000)
        state['framerate_step'] = camera.get_framerate_increment() if framerate_enabled else 0
        state['framerate_value'] = camera.get_framerate() if framerate_enabled else 0

        gain_enabled = camera.gain_available()
        state['gain_enabled'] = gain_enabled
        state['gain_min'], state['gain_max'] = camera.get_gain_range() if gain_enabled else (0,0)
        state['gain_step'] = camera.get_gain_increment() if gain_enabled else 0
        state['gain_value'] = camera.get_gain() if gain_enabled else 0

        exposure_enabled = camera.exposure_available()
        state['exposure_enabled'] = exposure_enabled
        state['exposure_min'], state['exposure_max'] = camera.get_exposure_range() if exposure_enabled else (0,0)
        state['exposure_step'] = camera.get_exposure_increment() if exposure_enabled else 0
        state['exposure_value'] = camera.get_exposure() if exposure_enabled else 0

        # NOTE offset range changes as a function of set (height, width)
        offsetX_enabled = camera.offsetX_available()
        state['offsetX_enabled'] = offsetX_enabled
        state['offsetX_min'], state['offsetX_max'] = camera.get_offsetX_range() if offsetX_enabled else (0,0)
        state['offsetX_step'] = camera.get_offsetX_increment() if offsetX_enabled else 0
        state['offsetX_value'] = camera.get_offsetX() if offsetX_enabled else 0

        offsetY_enabled = camera.offsetY_available()
        state['offsetY_enabled'] = offsetY_enabled
        state['offsetY_min'], state['offsetY_max'] = camera.get_offsetY_range() if offsetY_enabled else (0,0)
        state['offsetY_step'] = camera.get_offsetY_increment() if offsetY_enabled else 0
        state['offsetY_value'] = camera.get_offsetY() if offsetY_enabled else 0

        height_enabled = camera.height_available()
        state['height_enabled'] = height_enabled
        state['height_min'], state['height_max'] = camera.get_height_range() if height_enabled else (0,0)
        state['height_step'] = camera.get_height_increment() if height_enabled else 0
        state['height_value'] = camera.get_height() if height_enabled else 0

        width_enabled = camera.width_available()
        state['width_enabled'] = width_enabled
        state['width_min'], state['width_max'] = camera.get_width_range() if width_enabled else (0,0)
        state['width_step'] = camera.get_width_increment() if width_enabled else 0
        state['width_value'] = camera.get_width() if width_enabled else 0

        state['num_channels'] = camera.get_num_channels()
        
        return state

    def on_state_changed(self):
        # maybe do this for each property separately with specialized signals
        
        # stop preview
        preview_state = self.camera_preview_started
        if preview_state:
            self.set_preview(False)

        # set value
        camera = self.camera_constructor()
        state = self.view.get_state()

        camera.set_width(state['width_value'])
        camera.set_height(state['height_value'])
        camera.set_offsetY(state['offsetY_value'])
        camera.set_offsetX(state['offsetX_value'])
        camera.set_exposure(state['exposure_value'])
        camera.set_framerate(state['framerate_value'])
        camera.set_gain(state['gain_value'])
        
        # check values
        state_validated = self.get_camera_state(camera)

        del(camera)

        # report to the GUI to make sure hardware and GUI have the same info
        self.view.block_signals(True)
        self.view.set_state(state_validated)
        self.view.block_signals(False)

        # restart preview
        if preview_state:
            self.set_preview(True)

        self.state_changed.emit()

    def get_state(self):
        state = self.view.get_state()
        state['camera_constructor'] = self.camera_constructor 
        return state

    def set_preview(self, enable: bool):
        if enable:
            if not self.camera_preview_started:
                self.camera_preview_started = True
                self.acq = CameraAcquisition(self.camera_constructor, self.view)
                self.thread_pool.start(self.acq)
        else:
            if self.camera_preview_started:
                self.camera_preview_started = False
                self.acq.stop()
                self.thread_pool.waitForDone(-1)
        
if __name__ == "__main__":

    app = QApplication([])
    window = CameraWidget()
    controller = CameraController(window)
    window.show()
    app.exec()
