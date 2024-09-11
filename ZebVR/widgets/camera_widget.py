from typing import Dict
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFileDialog
from qt_widgets import LabeledDoubleSpinBox, LabeledSliderDoubleSpinBox, LabeledSpinBox, NDarray_to_QPixmap
from numpy.typing import NDArray
from PyQt5.QtCore import pyqtSignal
import numpy as np
import cv2

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
        self.camera_choice.addItems(["XIMEA", "Webcam", "Movie"])
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

    def set_image(self, image: NDArray):
        # TODO maybe check that image is uint8
        h, w = image.shape
        preview_width = int(w * self.PREVIEW_HEIGHT/h)
        image_resized = cv2.resize(image,(preview_width, self.PREVIEW_HEIGHT), cv2.INTER_NEAREST)
        self.image.setPixmap(NDarray_to_QPixmap(image_resized))

    def camera_changed(self):
        name = self.camera_choice.currentText()
        id = self.camera_id.value() 
        filename = self.filename.text()

        self.camera_source.emit(name, id, filename)

        if name in ["XIMEA", "Webcam"]:
            self.camera_id.setEnabled(True)
            self.movie_load.setEnabled(False)
        else:
            self.camera_id.setEnabled(False)
            self.movie_load.setEnabled(True)

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

        layout_controls = QVBoxLayout(self)
        layout_controls.addWidget(self.camera_choice)
        layout_controls.addLayout(layout_cam)

        for control in self.controls:
            spinbox = getattr(self, control + '_spinbox')
            layout_controls.addWidget(spinbox)

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
        for control in self.controls:
            spinbox = getattr(self, control + '_spinbox')
            state[control + '_enabled'] = spinbox.isEnabled()
            state[control + '_min'] = spinbox.minimum()
            state[control + '_max'] = spinbox.maximum()
            state[control + '_step'] = spinbox.singleStep()
            state[control + '_value'] = spinbox.value()
        return state
    
    def set_state(self, state: Dict) -> None:

        try:
            for control in self.controls:
                spinbox = getattr(self, control + '_spinbox')
                spinbox.setEnabled(state[control + '_enabled'])
                spinbox.setMinimum(state[control + '_min'])
                spinbox.setMaximum(state[control + '_max'])
                spinbox.setSingleStep(state[control + '_step'])
                spinbox.setValue(state[control + '_value'])

        except KeyError:
            print('Wrong state provided to camera widget')
            raise

if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication, QMainWindow
    from PyQt5.QtCore import  QRunnable, QThreadPool
    from camera_tools import Camera, OpenCV_Webcam, MovieFileCam

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
                        self.widget.set_image(frame['image'])
                except:
                    pass
            self.camera.stop_acquisition()

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
            elif name=='Movie':
                self.camera = MovieFileCam(filename)
            elif name=='XIMEA' and XIMEA_ENABLED:
                self.camera = XimeaCamera(dev_id=id)

            # read camera properties and set widget state accordingly

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
