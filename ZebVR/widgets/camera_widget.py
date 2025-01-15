from typing import Dict
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFileDialog
from PyQt5.QtCore import pyqtSignal, QRunnable
from PyQt5.QtGui import QImage
from qt_widgets import LabeledDoubleSpinBox, LabeledSpinBox, NDarray_to_QPixmap
from numpy.typing import NDArray
import numpy as np
import cv2
import os
from camera_tools import Camera


class CameraWidget(QWidget):

    state_changed = pyqtSignal()
    preview = pyqtSignal(bool)
    camera_source = pyqtSignal(str, int, str)
    PREVIEW_HEIGHT: int = 512

    def __init__(self,*args,**kwargs):

        super().__init__(*args, **kwargs)
        
        self.controls = [
            'framerate', 
            'exposure', 
            'gain', 
            'offsetX', 
            'offsetY', 
            'height',
            'width'
        ]

        self.updated = False
        self.declare_components()
        self.layout_components()
        self.setWindowTitle('Camera controls')

    def declare_components(self):

        self.camera_choice = QComboBox()
        self.camera_choice.addItems(["None", "XIMEA", "Webcam", "Webcam (Registration Mode)", "Movie"])
        self.camera_choice.currentTextChanged.connect(self.camera_changed)

        self.camera_id = LabeledSpinBox()
        self.camera_id.setText('Camera ID:')
        self.camera_id.setEnabled(True)
        self.camera_id.valueChanged.connect(self.camera_changed)
        
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
            spinbox.valueChanged.connect(self.on_change)

        self.num_channels_label = QLabel()
        self.num_channels_label.setText('Num channels:')
        self.num_channels = QLabel()
        self.num_channels.setText('0')

        # image
        self.preview_start = QPushButton('start preview')
        self.preview_start.clicked.connect(self.start)

        self.preview_stop = QPushButton('stop preview')
        self.preview_stop.clicked.connect(self.stop)

        self.image = QLabel()
        self.set_image(np.zeros((512,512), dtype=np.uint8))

    def load_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "Load movie",
            "",
            "Movie file (*.avi)"
        )
        self.filename.setText(filename)
        self.camera_changed()

    def start(self):
        self.preview.emit(True)

    def stop(self):
        self.preview.emit(False)

    def set_image(self, image_rgb: NDArray):
        # TODO maybe check that image is uint8
        h, w = image_rgb.shape[:2]
        preview_width = int(w * self.PREVIEW_HEIGHT/h)
        image_resized = cv2.resize(image_rgb,(preview_width, self.PREVIEW_HEIGHT), cv2.INTER_NEAREST)
        pixmap = NDarray_to_QPixmap(image_resized, format = QImage.Format_RGB888)
        self.image.setPixmap(pixmap)

    def camera_changed(self):
        name = self.camera_choice.currentText()
        id = self.camera_id.value() 
        filename = self.filename.text()

        self.camera_source.emit(name, id, filename)

        if name == 'Movie':
            self.camera_id.setEnabled(False)
            self.movie_load.setEnabled(True)
        else:
            self.camera_id.setEnabled(True)
            self.movie_load.setEnabled(False)

        self.state_changed.emit()

    def layout_components(self):

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
        layout_controls.addWidget(self.camera_choice)
        layout_controls.addLayout(layout_cam)

        for control in self.controls:
            spinbox = getattr(self, control + '_spinbox')
            layout_controls.addWidget(spinbox)

        layout_controls.addLayout(layout_channels)
        layout_controls.addLayout(layout_buttons)
        layout_controls.addWidget(self.image)
        layout_controls.addStretch()

    def on_change(self):
        self.updated = True
        self.state_changed.emit()

    def block_signals(self, block):
        for widget in self.findChildren(QWidget):
            widget.blockSignals(block)

    def is_updated(self) -> bool:
        return self.updated
    
    def set_updated(self, updated:bool) -> None:
        self.updated = updated

    def get_state(self) -> Dict:

        state = {}
        state['camera_choice'] = self.camera_choice.currentText()
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

        try:
            self.camera_id.setValue(state['camera_index'])
            self.filename.setText(state['movie_file'])
            self.camera_choice.setCurrentText(state['camera_choice'])
            for control in self.controls:
                spinbox = getattr(self, control + '_spinbox')
                spinbox.setRange(state[control + '_min'], state[control + '_max'])
                spinbox.setSingleStep(state[control + '_step'])
                spinbox.setValue(state[control + '_value'])
                spinbox.setEnabled(state[control + '_enabled'])
            self.num_channels.setText(str(state['num_channels']))
        except KeyError:
            print('Wrong state provided to camera widget')
            raise

#TODO add camera controller (MVC) as a bridge between Camera and CameraWidget
class CameraController:

    def __init__(self, model: Camera, view: CameraWidget):
        self.model = model
        self.view = view

        # connect view signals to controller methods
    
         

class CameraAcquisition(QRunnable):

    def __init__(self, camera_constructor: Camera, widget: CameraWidget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.camera_constructor = camera_constructor
        self.widget = widget
        self.keepgoing = True
        
    def stop(self):
        self.keepgoing = False
    
    def run(self):
        camera = self.camera_constructor()
        state = self.widget.get_state()
        camera.set_height(state['height_value'])
        camera.set_width(state['width_value'])
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
            except:
                pass
        camera.stop_acquisition()
        

if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication, QMainWindow
    from PyQt5.QtCore import  QRunnable, QThreadPool
    from camera_tools import Camera, OpenCV_Webcam, MovieFileCam

    try:
        from camera_tools import XimeaCamera
        XIMEA_ENABLED = True
    except ImportError:
        XIMEA_ENABLED = False

    class Window(QMainWindow):
        def __init__(self,*args,**kwargs):

            super().__init__(*args, **kwargs)
            self.camera = None
            self.preview_started = False # maybe move that out of here and to the code that handles the camera
            self.camera_widget = CameraWidget()
            self.camera_widget.camera_source.connect(self.set_camera)
            self.camera_widget.preview.connect(self.preview)
            self.camera_widget.state_changed.connect(self.update_camera_settings)
            self.thread_pool = QThreadPool()
            self.acq = None
            self.setCentralWidget(self.camera_widget)
        
        def set_camera(self, name: str, id: int, filename: str):
            
            if name=='Webcam':
                self.camera = OpenCV_Webcam(cam_id=id)
            elif name=='Movie' and os.path.exists(filename):
                self.camera = MovieFileCam(filename)
            elif name=='XIMEA' and XIMEA_ENABLED:
                self.camera = XimeaCamera(dev_id=id)

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

            state['num_channels'] = self.camera.get_num_channels()
            
            self.camera_widget.set_state(state)

        def update_camera_settings(self):
            state = self.camera_widget.get_state()
            # update camera

        def get_camera_properties(self):
            # TODO I was here
            state = {}
            state['framerate_value'] = self.camera.get_framerate()
            return state

        def preview(self, enable: bool):
            if enable:
                if not self.preview_started:
                    self.preview_started = True
                    self.acq = CameraAcquisition(self.camera, self.camera_widget)
                    self.thread_pool.start(self.acq)
            else:
                if self.preview_started:
                    self.preview_started = False
                    self.acq.stop()

    app = QApplication([])
    window = Window()
    window.show()
    app.exec()
