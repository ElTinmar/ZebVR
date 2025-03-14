from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QCheckBox
from PyQt5.QtCore import pyqtSignal, QObject, QRunnable, QThreadPool
from typing import Dict, Optional, Callable
from viewsonic_serial import ViewSonicProjector, ConnectionFailed, SourceInput, Bool
import time
from qt_widgets import LabeledDoubleSpinBox, LabeledSpinBox
from functools import partial
class ProjectorWidget(QWidget):

    state_changed = pyqtSignal()
    active_signal = pyqtSignal(bool)
    projector_state_changed = pyqtSignal()
    power_on_signal = pyqtSignal()
    power_off_signal = pyqtSignal()
    scale_tooltip = "Used for non-rectangular micromirror arrays (e.g. Lightcrafters)"

    def __init__(self,*args,**kwargs):

        super().__init__(*args, **kwargs)

        self.declare_components()
        self.layout_components()
    
    def declare_components(self):

        self.proj_height = LabeledSpinBox()
        self.proj_height.setText('height:')
        self.proj_height.setRange(1, 10_000)
        self.proj_height.setValue(1080)
        self.proj_height.valueChanged.connect(self.state_changed.emit)

        self.proj_width = LabeledSpinBox()
        self.proj_width.setText('width:')
        self.proj_width.setRange(1, 10_000)
        self.proj_width.setValue(1920)
        self.proj_width.valueChanged.connect(self.state_changed.emit)

        self.offset_x = LabeledSpinBox()
        self.offset_x.setText('offset X:')
        self.offset_x.setRange(0, 100_000)
        self.offset_x.setValue(1080)
        self.offset_x.valueChanged.connect(self.state_changed.emit)
    
        self.offset_y = LabeledSpinBox()
        self.offset_y.setText('offset Y:')
        self.offset_y.setRange(0, 100_000)
        self.offset_y.setValue(0)
        self.offset_y.valueChanged.connect(self.state_changed.emit)

        self.proj_fps = LabeledSpinBox()
        self.proj_fps.setText('FPS:')
        self.proj_fps.setRange(0, 960)
        self.proj_fps.setValue(240)
        self.proj_fps.valueChanged.connect(self.state_changed.emit)

        self.scale_x = LabeledDoubleSpinBox()
        self.scale_x.setText('scale X:')
        self.scale_x.setValue(1.0)
        self.scale_x.setSingleStep(0.05)
        self.scale_x.valueChanged.connect(self.state_changed.emit)
        self.scale_x.setToolTip(self.scale_tooltip)

        self.scale_y = LabeledDoubleSpinBox()
        self.scale_y.setText('scale Y:')
        self.scale_y.setValue(1.0)
        self.scale_y.setSingleStep(0.05)
        self.scale_y.valueChanged.connect(self.state_changed.emit)
        self.scale_y.setToolTip(self.scale_tooltip)

        # Serial communication with the projector
        self.power_on = QPushButton('Power On')
        self.power_on.clicked.connect(self.power_on_signal.emit)

        self.power_off = QPushButton('Power Off')
        self.power_off.clicked.connect(self.power_off_signal.emit)

        self.video_source = QComboBox()
        for src in SourceInput:
            self.video_source.addItem(str(src))
        self.video_source.currentTextChanged.connect(self.projector_state_changed.emit)

        self.fast_input_mode = QCheckBox('Fast input mode')
        self.fast_input_mode.stateChanged.connect(self.projector_state_changed.emit)

        self.serial_number = QLabel('S/N:') 
        self.power_status = QLabel('Power:')
        self.temperature = QLabel(u'Temperature (\N{DEGREE SIGN}C)')
        self.last_refresh_time = QLabel('Last refresh:')

    def layout_components(self):

        resolution_layout = QHBoxLayout() 
        resolution_layout.addWidget(self.proj_width)
        resolution_layout.addWidget(self.proj_height)

        offset_layout = QHBoxLayout() 
        offset_layout.addWidget(self.offset_x)
        offset_layout.addWidget(self.offset_y)

        scale_layout = QHBoxLayout()
        scale_layout.addWidget(self.scale_x)
        scale_layout.addWidget(self.scale_y)

        power_layout = QHBoxLayout()
        power_layout.addWidget(self.power_on)
        power_layout.addWidget(self.power_off)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(resolution_layout)
        main_layout.addLayout(offset_layout)
        main_layout.addLayout(scale_layout)
        main_layout.addWidget(self.proj_fps)
        main_layout.addSpacing(20)
        main_layout.addLayout(power_layout)
        main_layout.addWidget(self.video_source)
        main_layout.addWidget(self.fast_input_mode)
        main_layout.addWidget(self.power_status)
        main_layout.addWidget(self.serial_number)
        main_layout.addWidget(self.temperature)
        main_layout.addWidget(self.last_refresh_time)
        main_layout.addStretch()

    def block_signals(self, block):
        for widget in self.findChildren(QWidget):
            widget.blockSignals(block)

    def get_state(self) -> Dict:
        state = {}
        state['resolution'] = (self.proj_width.value(), self.proj_height.value())
        state['offset'] = (self.offset_x.value(), self.offset_y.value())
        state['pixel_scale'] = (self.scale_x.value(), self.scale_y.value())
        state['fps'] = self.proj_fps.value()
        
        return state
    
    def set_state(self, state: Dict) -> None:
        
        setters = {
            'resolution': lambda x: (
                self.proj_width.setValue(x[0]),
                self.proj_height.setValue(x[1])
            ),
            'offset': lambda x: (
                self.offset_x.setValue(x[0]),
                self.offset_y.setValue(x[1])
            ),
            'pixel_scale': lambda x: (
                self.scale_x.setValue(x[0]),
                self.scale_y.setValue(x[1])
            ),
            'fps': self.proj_fps.setValue   
        }

        for key, setter in setters.items():
            if key in state:
                setter(state[key])

    def get_projector_state(self) -> Dict:
        state = {}
        state['video_source'] = self.video_source.currentText()
        state['fast_input_mode'] = self.fast_input_mode.isChecked()
        state['serial_number'] = self.serial_number.text()
        state['power_status'] = self.power_status.text()
        state['temperature'] = self.temperature.text()
        state['last_refresh'] = self.last_refresh_time.text()
        return state

    def set_projector_state(self, state: Dict) -> None:
        self.video_source.setCurrentText(state['video_source'])
        self.fast_input_mode.setChecked(state['fast_input_mode'])
        self.serial_number.setText(f"S/N:{state['serial_number']}")
        self.power_status.setText(f"Power:{state['power_status']}")
        self.temperature.setText(f"Temperature:{state['temperature']}\N{DEGREE SIGN}C")
        self.last_refresh_time.setText(f"Last refresh:{state['last_refresh']}")

    def closeEvent(self, event):
        # If widget is a children of some other widget, it needs
        # to be explicitly closed for this to happen
        self.active_signal.emit(False)


class ProjectorChecker(QRunnable):

    def __init__(
            self, 
            projector_constructor: Callable[[], ViewSonicProjector], 
            widget: ProjectorWidget, 
            refresh_rate: float = 1,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.projector_constructor = projector_constructor
        self.widget = widget
        self.refresh_rate = refresh_rate
        self.keepgoing = True

    def stop(self):
        self.keepgoing = False

    def run(self):
        try:
            projector = self.projector_constructor()
        except ConnectionFailed:
            print('No projector was found')
            return

        while self.keepgoing:

            state = {}
            try:
                state['power_status'] = str(projector.get_power_status())
            except:
                continue

            try:                
                state['video_source'] = str(projector.get_source_input())
                state['fast_input_mode'] = bool(projector.get_fast_input_mode())
                state['serial_number'] = projector.get_serial_number()
                state['temperature'] = str(projector.get_operating_temperature())
                state['last_refresh'] = time.asctime()

            except:
                state['video_source'] = 'NONE'
                state['fast_input_mode'] = False
                state['serial_number'] = ''
                state['temperature'] = ''
                state['last_refresh'] = time.asctime()
            
            self.widget.block_signals(True)
            self.widget.set_projector_state(state)
            self.widget.block_signals(False)

            time.sleep(1/self.refresh_rate)
        

class ProjectorController(QObject):

    state_changed = pyqtSignal()

    def __init__(self, view: ProjectorWidget, *args, **kwargs):
        
        super().__init__(*args, **kwargs)

        self.view = view
        self.projector_checker_started = False
        self.thread_pool = QThreadPool()
        self.checker = None

        self.projector_constructor = partial(ViewSonicProjector, verbose=False) # TODO make a widget selection for this. Add None and gray out panel
        self.view.state_changed.connect(self.state_changed.emit)
        self.view.projector_state_changed.connect(self.on_state_changed)
        self.view.power_on_signal.connect(self.power_on)
        self.view.power_off_signal.connect(self.power_off)
        self.view.active_signal.connect(self.set_checker)

        self.set_checker(True)

    def power_on(self):
        self.set_checker(False)

        try:
            projector = self.projector_constructor()
        except ConnectionFailed:
            return
        
        projector.power_on()
        self.on_state_changed()
        self.set_checker(True)

    def power_off(self):
        self.set_checker(False)

        try:
            projector = self.projector_constructor()
        except ConnectionFailed:
            return

        projector.power_off()
        self.set_checker(True)

    def get_projector_state(self, projector: ViewSonicProjector) -> Optional[Dict]: # TODO write a Projector protocol
        state = {}
        state['power_status'] = str(projector.get_power_status())
        state['video_source'] = str(projector.get_source_input())
        state['fast_input_mode'] = bool(projector.get_fast_input_mode())
        state['serial_number'] = projector.get_serial_number()
        state['temperature'] = str(projector.get_operating_temperature())
        return state

    def set_checker(self, enable: bool):
        if enable:
            if not self.projector_checker_started:
                self.projector_checker_started = True
                self.checker = ProjectorChecker(self.projector_constructor, self.view, 1)
                self.thread_pool.start(self.checker)
        else:
            if self.projector_checker_started:
                self.projector_checker_started = False
                self.checker.stop()
                self.thread_pool.waitForDone(-1)

    def on_state_changed(self):

        # stop checker
        self.set_checker(False)

        # set value
        try:
            projector = self.projector_constructor()
        except ConnectionFailed:
            return
        
        state = self.view.get_projector_state()

        src = SourceInput[state['video_source']]
        fast_input = Bool.ON if state['fast_input_mode'] else Bool.OFF
        try:
            projector.set_source_input(src)
            projector.set_fast_input_mode(fast_input)
        except:
            pass

        # check values
        state_validated = self.get_projector_state(projector)
        state_validated['last_refresh'] = time.asctime()

        del(projector)

        # report to the GUI to make sure hardware and GUI have the same info
        self.view.block_signals(True)
        self.view.set_projector_state(state_validated)
        self.view.block_signals(False)

        # restart checker
        self.set_checker(True)

    def get_state(self):
        state = self.view.get_state()
        state['projector_constructor'] = self.projector_constructor 
        return state

if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication, QMainWindow
    from PyQt5.QtCore import  QRunnable, QThreadPool

    class Window(QMainWindow):

        def __init__(self,*args,**kwargs):

            super().__init__(*args, **kwargs)
            self.projector_widget = ProjectorWidget()
            self.setCentralWidget(self.projector_widget)
    
    app = QApplication([])
    window = Window()
    window.show()
    app.exec()
