from pathlib import Path
from functools import partial
from typing import Dict, Callable, Union
from enum import IntEnum
import time

from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLabel, 
    QPushButton, 
    QComboBox, 
    QFileDialog,
    QGraphicsScene, 
    QGraphicsPixmapItem,
    QApplication
)
from PyQt5.QtCore import (
    pyqtSignal, 
    QObject, 
    QTimer, 
    Qt, 
    QThread,
    QEventLoop
)
from PyQt5.QtGui import QImage
from numpy.typing import NDArray
import numpy as np

from qt_widgets import (
    LabeledDoubleSpinBox, 
    LabeledSpinBox, 
    LabeledComboBox,
    NDarray_to_QPixmap, 
    ZoomableGraphicsView
)

from camera_tools import (
    Camera, 
    OpenCV_Webcam, 
    OpenCV_Webcam_Gray,
    OpenCV_Webcam_InitEveryFrame, 
    MovieFileCam, 
    MovieFileCamGray,
    ZeroCam
)
try:
    from camera_tools import XimeaCamera_Transport
    XIMEA_ENABLED = True
except ImportError:
    XIMEA_ENABLED = False
try:
    from camera_tools import SpinnakerCamera
    SPINNAKER_ENABLED = True
except ImportError:
    SPINNAKER_ENABLED = False

class CameraModel(IntEnum):
    ZERO_GRAY = 0
    ZERO_RGB = 1
    WEBCAM = 2
    WEBCAM_GRAY = 3
    WEBCAM_REGISTRATION = 4
    XIMEA = 5
    SPINNAKER = 6
    MOVIE = 7
    MOVIE_GRAY = 8

WEBCAMS = [CameraModel.WEBCAM, CameraModel.WEBCAM_GRAY, CameraModel.WEBCAM_REGISTRATION]
MOVIES = [CameraModel.MOVIE, CameraModel.MOVIE_GRAY]

class CameraWidget(QWidget):

    source_changed = pyqtSignal(int, int, str)
    state_changed = pyqtSignal()
    preview = pyqtSignal(bool)
    stop_signal = pyqtSignal()
    webcam_modes_set = pyqtSignal()
    update_done = pyqtSignal()

    PREVIEW_HEIGHT: int = 480
    REFRESH_RATE = 60

    def __init__(self, *args, **kwargs):

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
        self.current_preview_width = self.PREVIEW_HEIGHT
        self.current_width = self.PREVIEW_HEIGHT
        self.current_height = self.PREVIEW_HEIGHT
        self.webcam_modes = {}

        self.declare_components()
        self.layout_components()
        self.setWindowTitle('Camera controls')

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.set_pixmap)
        self.timer.start(1000//self.REFRESH_RATE) 

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
            else:
                continue

            setattr(self, control + '_spinbox', constructor())
            spinbox = getattr(self, control + '_spinbox')
            spinbox.setText(control)
            spinbox.setRange(0,0)
            spinbox.setSingleStep(0)
            spinbox.setValue(0)
            spinbox.setEnabled(False)
            spinbox.valueChanged.connect(self.state_changed)

        self.webcam_format = LabeledComboBox()
        self.webcam_format.setText('Format:')
        self.webcam_format.currentIndexChanged.connect(self.webcam_format_changed)
        self.webcam_format.setVisible(False)
        self.webcam_format.setEnabled(False)

        self.webcam_resolution = LabeledComboBox()
        self.webcam_resolution.setText('Resolution:')
        self.webcam_resolution.currentIndexChanged.connect(self.webcam_resolution_changed)
        self.webcam_resolution.setVisible(False)

        self.webcam_framerate = LabeledComboBox()
        self.webcam_framerate.setText('Framerate:')
        self.webcam_framerate.currentIndexChanged.connect(self.webcam_framerate_changed)
        self.webcam_framerate.setVisible(False)

        self.num_channels_label = QLabel()
        self.num_channels_label.setText('Num channels:')
        self.num_channels = QLabel()
        self.num_channels.setText('0')

        # image
        self.preview_start = QPushButton('start preview')
        self.preview_start.clicked.connect(self.start)

        self.preview_stop = QPushButton('stop preview')
        self.preview_stop.clicked.connect(self.stop)

        self.scene = QGraphicsScene(self)
        self.image_item = QGraphicsPixmapItem()
        self.scene.addItem(self.image_item)
        self.image_view = ZoomableGraphicsView(self.scene)
        self.image_view.setFixedHeight(self.PREVIEW_HEIGHT)
        self.image_view.setFixedWidth(self.PREVIEW_HEIGHT)
        self.image_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.image_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def load_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "Load movie",
            "",
            ""
        )
        self.filename.setText(filename)
        self.on_source_change()

    def set_webcam_modes(self, modes: Dict):
        self.webcam_modes = modes

        self.block_signals(True)
        self.webcam_format.clear()
        self.webcam_resolution.clear()
        self.webcam_framerate.clear()
        self.block_signals(False)
        
        if not modes:
            return
        
        self.block_signals(True)
        for fmt, config_width in modes.items():
            self.webcam_format.addItem(str(fmt), fmt)
        self.webcam_format.setCurrentData(fmt)

        for width, config_height in config_width.items():
            for height, framerates in config_height.items():
                self.webcam_resolution.addItem(f'{width}x{height}', (width, height))
        self.webcam_resolution.setCurrentData((width, height))
        self.width_spinbox.setValue(width)
        self.height_spinbox.setValue(height)

        for fps in framerates:
            self.webcam_framerate.addItem(str(fps), fps)
        self.webcam_framerate.setCurrentData(fps)
        self.framerate_spinbox.setValue(fps)
        self.block_signals(False)
        
        self.webcam_modes_set.emit()

    def webcam_format_changed(self):
        
        if not self.webcam_modes:
            return
        
        fmt = self.webcam_format.currentData()
        config_width = self.webcam_modes[fmt]

        self.block_signals(True)
        self.webcam_resolution.clear()
        self.webcam_framerate.clear()

        for width, config_height in config_width.items():
            for height, framerates in config_height.items():
                self.webcam_resolution.addItem(f'{width}x{height}', (width, height))
        self.webcam_resolution.setCurrentData((width, height))
        self.width_spinbox.setValue(width)
        self.height_spinbox.setValue(height)
        
        for fps in framerates:
            self.webcam_framerate.addItem(str(fps), fps)
        self.webcam_framerate.setCurrentData(fps)
        self.framerate_spinbox.setValue(fps)

        self.block_signals(False)
        self.state_changed.emit()

    def webcam_resolution_changed(self):

        if not self.webcam_modes:
            return
        
        fmt = self.webcam_format.currentData()
        width, height = self.webcam_resolution.currentData()
        
        self.block_signals(True)

        self.width_spinbox.setValue(width)
        self.height_spinbox.setValue(height)

        framerates = self.webcam_modes[fmt][width][height]
        self.webcam_framerate.clear()
        for fps in framerates:
            self.webcam_framerate.addItem(str(fps), fps)
        self.webcam_framerate.setCurrentData(fps)
        self.framerate_spinbox.setValue(fps)

        self.block_signals(False)
        self.state_changed.emit()

    def webcam_framerate_changed(self):
        fps = self.webcam_framerate.currentData()
        self.block_signals(True)
        self.framerate_spinbox.setValue(fps)
        self.block_signals(False)
        self.state_changed.emit()

    def start(self):
        self.preview.emit(True)

    def stop(self):
        self.preview.emit(False)

    def set_image(self, image: NDArray):
        self.image = image

    def set_pixmap(self):

        h, w = self.image.shape[:2]
        pixmap = NDarray_to_QPixmap(self.image, format = QImage.Format_RGB888)
        self.image_item.setPixmap(pixmap)

        # check if shape has changed
        if h != self.current_height or w != self.current_width:
            self.current_height = h
            self.current_width = w
            preview_width = int(w * self.PREVIEW_HEIGHT/h)
            self.current_preview_width = preview_width

            self.image_view.setFixedWidth(self.current_preview_width)
            self.image_view.fitInView(self.image_item, Qt.KeepAspectRatio)
            self.image_view.centerOn(self.image_item)
            self.scene.setSceneRect(self.image_item.boundingRect())

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
        layout_controls.addWidget(self.webcam_format)
        layout_controls.addWidget(self.webcam_resolution)
        layout_controls.addWidget(self.webcam_framerate)

        for control in self.controls:
            spinbox = getattr(self, control + '_spinbox')
            layout_controls.addWidget(spinbox)

        layout_image = QHBoxLayout()
        layout_image.addStretch()
        layout_image.addWidget(self.image_view)
        layout_image.addStretch()

        layout_controls.addLayout(layout_channels)
        layout_controls.addLayout(layout_buttons)
        layout_controls.addStretch()
        layout_controls.addLayout(layout_image)
        layout_controls.addStretch()

    def on_source_change(self):
        # TODO show different widgets for webcam (format/res/fps), movie, ...

        model = self.camera_model.currentIndex()
        id = self.camera_id.value() 
        filename = self.filename.text()

        if model in MOVIES:
            self.camera_id.setEnabled(False)
            self.movie_load.setEnabled(True)
        else:
            self.camera_id.setEnabled(True)
            self.movie_load.setEnabled(False)

        if model in WEBCAMS:
            self.webcam_format.setVisible(True)
            self.webcam_resolution.setVisible(True)
            self.webcam_framerate.setVisible(True)
            self.width_spinbox.setVisible(False)
            self.height_spinbox.setVisible(False)
            self.framerate_spinbox.setVisible(False)
        else:
            self.webcam_format.setVisible(False)
            self.webcam_resolution.setVisible(False)
            self.webcam_framerate.setVisible(False)
            self.width_spinbox.setVisible(True)
            self.height_spinbox.setVisible(True)
            self.framerate_spinbox.setVisible(True)

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
    
    def update_state(self, state: Dict) -> None:

        self.block_signals(True)

        setters = {
            'camera_index': self.camera_id.setValue,
            'movie_file': lambda x: self.filename.setText(str(x)),
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

        self.block_signals(False)

        self.update_done.emit()
    
    def set_state(self, state: Dict) -> None:
        self.update_state(state)
        self.on_source_change()

    def closeEvent(self, event):
        self.stop_signal.emit()
        self.stop()

class CameraHandler(QObject):

    validated_state = pyqtSignal(dict)
    webcam_modes = pyqtSignal(dict)

    def __init__(self, view: CameraWidget, timer_update_ms: int = 1):

        super().__init__()
        
        self.view = view

        self.camera = None
        self.camera_constructor = None
        self.last_camera_state = None
        self.acquisition_started = False
        self.timer_update_ms = timer_update_ms

    def start_handler(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.get_frame)
        self.timer.start(self.timer_update_ms)  

    def stop_handler(self):
        self.timer.stop()
        if self.camera is not None:
            self.camera.stop_acquisition()
            del(self.camera)

    def frame_acquisition(self, enabled: bool):
        
        self.timer.stop()

        if self.camera is None:
            if self.camera_constructor is None:
                return
            
            if enabled:
                self.camera = self.camera_constructor()
        
        if enabled:
            if not self.acquisition_started:
                self.apply_state()
                self.camera.start_acquisition()
                self.acquisition_started = True
        else:
            if self.acquisition_started:
                self.camera.stop_acquisition()
                del(self.camera) 
                self.camera = None
                self.last_camera_state = None
                self.acquisition_started = False

        self.timer.start(self.timer_update_ms)
        
    def set_constructor(self, camera_constructor: Callable[[], Camera], camera_model: CameraModel):
        
        self.timer.stop()

        if self.camera is not None:
            self.camera.stop_acquisition()
            del(self.camera)

        self.camera_constructor = camera_constructor
        self.camera = self.camera_constructor()
        self.last_camera_state = None

        if camera_model in WEBCAMS:
            # wait until changes propagate in the GUI
            loop = QEventLoop()
            self.view.webcam_modes_set.connect(loop.quit)
            self.webcam_modes.emit(self.camera.supported_configs)
            loop.exec_()
            self.view.webcam_modes_set.disconnect(loop.quit)

        self.apply_state()

        if self.acquisition_started:
            self.camera.start_acquisition()

        self.timer.start(self.timer_update_ms)  

    def state_changed(self):
        self.timer.stop()
        self.apply_state()
        self.timer.start(self.timer_update_ms)

    def validate_state(self):

        if self.camera is None:
            return 
        
        state = {}

        width_enabled = self.camera.width_available()
        state['width_enabled'] = width_enabled
        state['width_min'], state['width_max'] = self.camera.get_width_range() if width_enabled else (0,0)
        state['width_step'] = self.camera.get_width_increment() if width_enabled else 0
        state['width_value'] = self.camera.get_width() if width_enabled else 0

        height_enabled = self.camera.height_available()
        state['height_enabled'] = height_enabled
        state['height_min'], state['height_max'] = self.camera.get_height_range() if height_enabled else (0,0)
        state['height_step'] = self.camera.get_height_increment() if height_enabled else 0
        state['height_value'] = self.camera.get_height() if height_enabled else 0

        framerate_enabled = self.camera.framerate_available()
        state['framerate_enabled'] = framerate_enabled
        state['framerate_min'], state['framerate_max'] = self.camera.get_framerate_range() if framerate_enabled else (0,10_000)
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

        # NOTE offset range changes as a function of set (height, width)
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

        state['num_channels'] = self.camera.get_num_channels()

        self.last_camera_state = state

        self.validated_state.emit(state)

    def requires_acquisition_restart(self, new_state: Dict) -> bool:
        
        if self.last_camera_state is None:
            return True
        
        width_changed = (new_state['width_value'] != self.last_camera_state['width_value'])
        height_changed = (new_state['height_value'] != self.last_camera_state['height_value'])
        offsetX_changed = (new_state['offsetX_value'] != self.last_camera_state['offsetX_value'])
        offsetY_changed = (new_state['offsetY_value'] != self.last_camera_state['offsetY_value'])
        return width_changed or height_changed or offsetX_changed or offsetY_changed

    def apply_state(self):

        if self.camera is None:
            return

        state = self.view.get_state()

        if self.requires_acquisition_restart(state):

            if self.acquisition_started:
                self.camera.stop_acquisition()

            self.camera.set_width(state['width_value'])
            self.camera.set_height(state['height_value'])
            self.camera.set_offsetX(state['offsetX_value'])
            self.camera.set_offsetY(state['offsetY_value'])

            if self.acquisition_started:
                self.camera.start_acquisition()
        
        self.camera.set_framerate(state['framerate_value'])
        self.camera.set_exposure(state['exposure_value'])
        self.camera.set_gain(state['gain_value'])

        # validate state
        self.validate_state()
    
    def get_frame(self):

        if self.camera is None:
            return

        if not self.acquisition_started:
            return

        try:                
            frame = self.camera.get_frame()
            if frame['image'] is not None:
                self.view.set_image(frame['image'])
        except Exception as e:
            print(f'Caught exception: {e}')               

class CameraController(QObject):

    state_changed = pyqtSignal()
    preview = pyqtSignal(bool)
    constructor_changed = pyqtSignal(object, object)

    def __init__(self, view: CameraWidget, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.view = view
        self.camera_constructor = None

        self.camera_thread = QThread()
        self.camera_handler = CameraHandler(self.view)
        self.camera_handler.moveToThread(self.camera_thread)

        # wire up signals and slots
        self.camera_handler.validated_state.connect(self.view.update_state)
        self.camera_handler.webcam_modes.connect(self.view.set_webcam_modes)
        self.camera_thread.started.connect(self.camera_handler.start_handler)

        self.view.source_changed.connect(self.on_source_changed)
        self.view.state_changed.connect(self.camera_handler.state_changed)
        self.view.state_changed.connect(self.state_changed)
        self.view.update_done.connect(self.state_changed)
        self.view.webcam_modes_set.connect(self.state_changed)
        self.view.preview.connect(self.camera_handler.frame_acquisition)
        self.view.stop_signal.connect(self.camera_handler.stop_handler)
        self.view.stop_signal.connect(self.stop)

        self.preview.connect(self.camera_handler.frame_acquisition)
        self.constructor_changed.connect(self.camera_handler.set_constructor)
        
        self.camera_thread.start()

        self.view.on_source_change()

    def on_source_changed(
            self, 
            camera_model: int, 
            camera_index: int, 
            filename: Union[Path, str]
        ):

        filename = Path(filename)

        if camera_model==CameraModel.ZERO_GRAY:
            self.camera_constructor = partial(ZeroCam, shape=(2048,2048), dtype=np.uint8)
        
        elif camera_model==CameraModel.ZERO_RGB:
            self.camera_constructor = partial(ZeroCam, shape=(2048,2048,3), dtype=np.uint8)

        elif camera_model==CameraModel.WEBCAM:
            self.camera_constructor = partial(OpenCV_Webcam, cam_id=camera_index)

        elif camera_model==CameraModel.WEBCAM_GRAY:
            self.camera_constructor = partial(OpenCV_Webcam_Gray, cam_id=camera_index)
        
        elif camera_model==CameraModel.WEBCAM_REGISTRATION:
            self.camera_constructor = partial(OpenCV_Webcam_InitEveryFrame, cam_id=camera_index)
        
        elif camera_model==CameraModel.SPINNAKER and SPINNAKER_ENABLED:
            self.camera_constructor = partial(SpinnakerCamera, dev_id=camera_index)

        elif camera_model==CameraModel.MOVIE:
            if not filename.is_file():
                return
            
            self.camera_constructor = partial(MovieFileCam, filename=str(filename))

        elif camera_model==CameraModel.MOVIE_GRAY:
            if not filename.is_file():
                return
            
            self.camera_constructor = partial(MovieFileCamGray, filename=str(filename))

        elif camera_model==CameraModel.XIMEA and XIMEA_ENABLED:
            self.camera_constructor = partial(XimeaCamera_Transport, dev_id=camera_index)

        if self.camera_constructor is not None:
            self.constructor_changed.emit(self.camera_constructor, camera_model)
            self.state_changed.emit()

    def set_preview(self, enable: bool):
        self.preview.emit(enable)

    def get_state(self):

        state = self.view.get_state()
        state['camera_constructor'] = self.camera_constructor 
        return state

    def stop(self):
        self.camera_thread.quit()
        self.camera_thread.wait()

if __name__ == "__main__":

    app = QApplication([])
    window = CameraWidget()
    controller = CameraController(window)
    window.show()
    app.exec()
