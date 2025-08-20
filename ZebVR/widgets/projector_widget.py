from PyQt5.QtWidgets import (
    QApplication, 
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLabel, 
    QPushButton, 
    QComboBox, 
    QCheckBox,
    QGroupBox
)
from PyQt5.QtCore import pyqtSignal, QObject, QThread, QTimer
from typing import Dict, List
from viewsonic_serial import ViewSonicProjector, SourceInput, Bool, Gamma, ColorMode
import time
from qt_widgets import LabeledDoubleSpinBox, LabeledSpinBox, LabeledSliderSpinBox, LabeledComboBox
from ..serial_utils import list_serial_devices, SerialDevice

class ProjectorWidget(QWidget):

    scale_tooltip = "Used for non-rectangular micromirror arrays (e.g. Lightcrafters)"
    REFRESH_RATE = 5

    state_changed = pyqtSignal()
    close_signal = pyqtSignal()

    serial_port_changed = pyqtSignal(str)
    power_on_signal = pyqtSignal()
    power_off_signal = pyqtSignal()
    video_source_changed = pyqtSignal(str)
    gamma_changed = pyqtSignal(str)
    color_mode_changed = pyqtSignal(str)
    fast_input_mode_changed = pyqtSignal(bool)
    red_gain_changed = pyqtSignal(int)
    red_offset_changed = pyqtSignal(int)
    green_gain_changed = pyqtSignal(int)
    green_offset_changed = pyqtSignal(int)
    blue_gain_changed = pyqtSignal(int)
    blue_offset_changed = pyqtSignal(int)

    def __init__(self,*args,**kwargs):

        super().__init__(*args, **kwargs)

        self.serial_devices: List[SerialDevice] = [SerialDevice()] + list_serial_devices()
        self.projector_state = {}
        self.declare_components()
        self.layout_components()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_projector_state)
        self.timer.start(int(1000//self.REFRESH_RATE)) 
    
    def declare_components(self) -> None:

        self.proj_height = LabeledSpinBox()
        self.proj_height.setText('height:')
        self.proj_height.setRange(1, 10_000)
        self.proj_height.setValue(1080)
        self.proj_height.valueChanged.connect(self.state_changed)

        self.proj_width = LabeledSpinBox()
        self.proj_width.setText('width:')
        self.proj_width.setRange(1, 10_000)
        self.proj_width.setValue(1920)
        self.proj_width.valueChanged.connect(self.state_changed)

        self.offset_x = LabeledSpinBox()
        self.offset_x.setText('offset X:')
        self.offset_x.setRange(0, 100_000)
        self.offset_x.setValue(1080)
        self.offset_x.valueChanged.connect(self.state_changed)
    
        self.offset_y = LabeledSpinBox()
        self.offset_y.setText('offset Y:')
        self.offset_y.setRange(0, 100_000)
        self.offset_y.setValue(0)
        self.offset_y.valueChanged.connect(self.state_changed)

        self.proj_fps = LabeledSpinBox()
        self.proj_fps.setText('FPS:')
        self.proj_fps.setRange(0, 960)
        self.proj_fps.setValue(240)
        self.proj_fps.valueChanged.connect(self.state_changed)

        self.scale_x = LabeledDoubleSpinBox()
        self.scale_x.setText('scale X:')
        self.scale_x.setValue(1.0)
        self.scale_x.setSingleStep(0.05)
        self.scale_x.valueChanged.connect(self.state_changed)
        self.scale_x.setToolTip(self.scale_tooltip)

        self.scale_y = LabeledDoubleSpinBox()
        self.scale_y.setText('scale Y:')
        self.scale_y.setValue(1.0)
        self.scale_y.setSingleStep(0.05)
        self.scale_y.valueChanged.connect(self.state_changed)
        self.scale_y.setToolTip(self.scale_tooltip)

        self.fullscreen = QCheckBox('fullscreen')
        self.fullscreen.setChecked(True)
        self.fullscreen.stateChanged.connect(self.state_changed)

        # Serial communication with the projector

        self.serial_group = QGroupBox('RS232 projector control')
        self.serial_group.setEnabled(False)

        self.refresh = QPushButton('Refresh serial devices')
        self.refresh.clicked.connect(self.refresh_serial)

        self.serial_ports = LabeledComboBox()
        self.serial_ports.setText('Serial port')
        self.serial_ports.currentIndexChanged.connect(self.serial_changed)
        for ser_port, description in self.serial_devices:
            self.serial_ports.addItem(f"{ser_port} - {description}")

        self.power_on = QPushButton('Power On')
        self.power_on.clicked.connect(self.power_on_signal)

        self.power_off = QPushButton('Power Off')
        self.power_off.clicked.connect(self.power_off_signal)

        self.video_source = LabeledComboBox()
        self.video_source.setText('Video source')
        for src in SourceInput:
            self.video_source.addItem(str(src))
        self.video_source.currentTextChanged.connect(self.video_source_changed)

        self.fast_input_mode = QCheckBox('Low latency mode')
        self.fast_input_mode.toggled.connect(self.fast_input_mode_changed)

        self.gamma = LabeledComboBox()
        self.gamma.setText('Gamma')
        for gamma in Gamma:
            self.gamma.addItem(str(gamma))
        self.gamma.currentTextChanged.connect(self.gamma_changed)

        self.color_mode = LabeledComboBox()
        self.color_mode.setText('Color mode')
        for cm in ColorMode:
            self.color_mode.addItem(str(cm))
        self.color_mode.currentTextChanged.connect(self.color_mode_changed)

        self.red_gain_slider = LabeledSliderSpinBox()
        self.red_gain_slider.setText('Red gain')
        self.red_gain_slider.setRange(0, 100)
        self.red_gain_slider.setSingleStep(1)
        self.red_gain_slider.setValue(50)
        self.red_gain_slider.valueChanged.connect(self.red_gain_changed)

        self.red_offset_slider = LabeledSliderSpinBox()
        self.red_offset_slider.setText('Red offset')
        self.red_offset_slider.setRange(-50, 50)
        self.red_offset_slider.setSingleStep(1)
        self.red_offset_slider.setValue(0)
        self.red_offset_slider.valueChanged.connect(self.red_offset_changed)

        self.green_gain_slider = LabeledSliderSpinBox()
        self.green_gain_slider.setText('Green gain')
        self.green_gain_slider.setRange(0, 100)
        self.green_gain_slider.setSingleStep(1)
        self.green_gain_slider.setValue(50)
        self.green_gain_slider.valueChanged.connect(self.green_gain_changed)

        self.green_offset_slider = LabeledSliderSpinBox()
        self.green_offset_slider.setText('Green offset')
        self.green_offset_slider.setRange(-50, 50)
        self.green_offset_slider.setSingleStep(1)
        self.green_offset_slider.setValue(0)
        self.green_offset_slider.valueChanged.connect(self.green_offset_changed)

        self.blue_gain_slider = LabeledSliderSpinBox()
        self.blue_gain_slider.setText('Blue gain')
        self.blue_gain_slider.setRange(0, 100)
        self.blue_gain_slider.setSingleStep(1)
        self.blue_gain_slider.setValue(50)
        self.blue_gain_slider.valueChanged.connect(self.blue_gain_changed)

        self.blue_offset_slider = LabeledSliderSpinBox()
        self.blue_offset_slider.setText('Blue offset')
        self.blue_offset_slider.setRange(-50, 50)
        self.blue_offset_slider.setSingleStep(1)
        self.blue_offset_slider.setValue(0)
        self.blue_offset_slider.valueChanged.connect(self.blue_offset_changed)

        self.serial_number = QLabel('S/N:') 
        self.power_status = QLabel('Power:')
        self.temperature = QLabel(u'Temperature (\N{DEGREE SIGN}C)')
        self.last_refresh_time = QLabel('Last refresh:')

    def serial_changed(self, index: int):
        port = self.serial_devices[index].device
        if port == '':
            self.serial_group.setEnabled(False)
            return
        
        self.serial_group.setEnabled(True)
        self.serial_port_changed.emit(port)

    def refresh_serial(self):
        self.serial_devices = [SerialDevice()] + list_serial_devices()
        self.serial_ports.clear()
        for ser_port, description in self.serial_devices:
            self.serial_ports.addItem(f"{ser_port} - {description}")

    def layout_components(self) -> None:

        resolution_layout = QHBoxLayout() 
        resolution_layout.addWidget(self.proj_width)
        resolution_layout.addWidget(self.proj_height)
        resolution_layout.setSpacing(50)

        offset_layout = QHBoxLayout() 
        offset_layout.addWidget(self.offset_x)
        offset_layout.addWidget(self.offset_y)
        offset_layout.setSpacing(50)

        scale_layout = QHBoxLayout()
        scale_layout.addWidget(self.scale_x)
        scale_layout.addWidget(self.scale_y)
        scale_layout.setSpacing(50)

        power_layout = QHBoxLayout()
        power_layout.addWidget(self.power_on)
        power_layout.addWidget(self.power_off)

        serial_layout = QVBoxLayout()
        serial_layout.addLayout(power_layout)
        serial_layout.addWidget(self.video_source)
        serial_layout.addWidget(self.gamma)
        serial_layout.addWidget(self.color_mode)
        serial_layout.addWidget(self.fast_input_mode)
        serial_layout.addWidget(self.red_gain_slider)
        serial_layout.addWidget(self.red_offset_slider)
        serial_layout.addWidget(self.green_gain_slider)
        serial_layout.addWidget(self.green_offset_slider)
        serial_layout.addWidget(self.blue_gain_slider)
        serial_layout.addWidget(self.blue_offset_slider)
        serial_layout.addWidget(self.power_status)
        serial_layout.addWidget(self.serial_number)
        serial_layout.addWidget(self.temperature)
        serial_layout.addWidget(self.last_refresh_time)
        self.serial_group.setLayout(serial_layout)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(resolution_layout)
        main_layout.addLayout(offset_layout)
        main_layout.addLayout(scale_layout)
        main_layout.addWidget(self.fullscreen)
        main_layout.addWidget(self.proj_fps)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.refresh)
        main_layout.addWidget(self.serial_ports)
        main_layout.addWidget(self.serial_group)
        main_layout.addStretch()

    def block_signals(self, block):
        for widget in self.findChildren(QWidget):
            widget.blockSignals(block)

    def get_state(self) -> Dict:
        state = {}
        state['resolution'] = (self.proj_width.value(), self.proj_height.value())
        state['offset'] = (self.offset_x.value(), self.offset_y.value())
        state['pixel_scale'] = (self.scale_x.value(), self.scale_y.value())
        state['fullscreen'] = self.fullscreen.isChecked()
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
            'fps': self.proj_fps.setValue,
            'fullscreen': self.fullscreen.setChecked,   
        }

        for key, setter in setters.items():
            if key in state:
                setter(state[key])

    def set_projector_state(self, state: Dict) -> None:
        self.projector_state = state

    def update_projector_state(self) -> None:

        setters = {
            'video_source': self.video_source.setCurrentText,
            'gamma': self.gamma.setCurrentText,
            'color_mode': self.color_mode.setCurrentText,
            'red_gain': self.red_gain_slider.setValue,
            'red_offset': self.red_offset_slider.setValue,
            'green_gain': self.green_gain_slider.setValue,
            'green_offset': self.green_offset_slider.setValue,
            'blue_gain': self.blue_gain_slider.setValue,
            'blue_offset': self.blue_offset_slider.setValue,
            'fast_input_mode': self.fast_input_mode.setChecked,
            'serial_number': lambda x: self.serial_number.setText(f"S/N:{x}"),
            'power_status': lambda x: self.power_status.setText(f"Power:{x}"),
            'temperature': lambda x: self.temperature.setText(f"Temperature:{x}\N{DEGREE SIGN}C"),
            'last_refresh': lambda x: self.last_refresh_time.setText(f"Last refresh:{x}")
        }

        self.block_signals(True)
        for key, setter in setters.items():
            if key in self.projector_state:
                setter(self.projector_state[key])
        self.block_signals(False)

    def closeEvent(self, event):
        self.close_signal.emit()


# TODO: not explicitly closing thread
class ProjectorController(QObject):

    state_changed = pyqtSignal()
    REFRESH_RATE: float = 1.0

    def __init__(self, view: ProjectorWidget, *args, **kwargs):
        
        super().__init__(*args, **kwargs)

        self.view = view
        self.projector = None
        
        self.thread = QThread()
        self.thread.started.connect(self.start_polling)
        self.thread.finished.connect(self.stop_polling)
        self.moveToThread(self.thread)

        self.view.state_changed.connect(self.state_changed)
        self.view.serial_port_changed.connect(self.serial_port_changed)
        self.view.video_source_changed.connect(self.change_video_source)
        self.view.gamma_changed.connect(self.change_gamma)
        self.view.color_mode_changed.connect(self.change_color_mode)
        self.view.fast_input_mode_changed.connect(self.change_fast_input_mode)
        self.view.power_on_signal.connect(self.power_on)
        self.view.power_off_signal.connect(self.power_off)
        self.view.red_gain_changed.connect(self.set_color_temperature_red_gain)
        self.view.red_offset_changed.connect(self.set_color_temperature_red_offset)
        self.view.green_gain_changed.connect(self.set_color_temperature_green_gain)
        self.view.green_offset_changed.connect(self.set_color_temperature_green_offset)
        self.view.blue_gain_changed.connect(self.set_color_temperature_blue_gain)
        self.view.blue_offset_changed.connect(self.set_color_temperature_blue_offset)

        self.thread.start()

    def start_polling(self):

        self.timer = QTimer()
        self.timer.timeout.connect(self.poll_state)
        self.timer.start(int(1000//self.REFRESH_RATE))  

    def stop_polling(self):
        
        self.timer.stop()

    def poll_state(self):

        if self.projector is None:
            return

        state = {}
        try:
            state['power_status'] = str(self.projector.get_power_status())
        except:
            return

        try:                
            state['video_source'] = str(self.projector.get_source_input())
            state['gamma'] = str(self.projector.get_gamma())
            state['color_mode'] = str(self.projector.get_color_mode())
            state['red_gain'] = self.projector.get_color_temperature_red_gain()
            state['red_offset'] = self.projector.get_color_temperature_red_offset()
            state['green_gain'] = self.projector.get_color_temperature_green_gain()
            state['green_offset'] = self.projector.get_color_temperature_green_offset()
            state['blue_gain'] = self.projector.get_color_temperature_blue_gain()
            state['blue_offset'] = self.projector.get_color_temperature_blue_offset()
            state['fast_input_mode'] = bool(self.projector.get_fast_input_mode())
            state['serial_number'] = self.projector.get_serial_number()
            state['temperature'] = str(self.projector.get_operating_temperature())
            state['last_refresh'] = time.asctime()

        except:
            state['video_source'] = 'NONE'
            state['gamma'] = 'GAMMA_1_8'
            state['color_mode'] = 'TV'
            state['red_gain'] = 50
            state['red_offset'] = 0
            state['green_gain'] = 50
            state['green_offset'] = 0
            state['blue_gain'] = 50
            state['blue_offset'] = 0
            state['fast_input_mode'] = False
            state['serial_number'] = ''
            state['temperature'] = ''
            state['last_refresh'] = time.asctime()
        
        self.view.set_projector_state(state)

    def change_video_source(self, video_source: str):

        if self.projector is None:
            return
        
        self.projector.set_source_input(SourceInput[video_source])

    def change_gamma(self, gamma: str):

        if self.projector is None:
            return
        
        self.projector.set_gamma(Gamma[gamma])

    def change_color_mode(self, color_mode: str):

        if self.projector is None:
            return
        
        self.projector.set_color_mode(ColorMode[color_mode])

    def change_fast_input_mode(self, fast_input_mode: bool):

        if self.projector is None:
            return

        fast_input = Bool.ON if fast_input_mode else Bool.OFF
        self.projector.set_fast_input_mode(fast_input)
  
    def serial_port_changed(self, port: str):

        if port == '':
            return

        self.projector = ViewSonicProjector(port=port, verbose=False) 

    def set_color_temperature_red_gain(self, gain: int):

        if self.projector is None:
            return
        
        self.projector.set_color_temperature_red_gain(gain)

    def set_color_temperature_red_offset(self, offset: int):

        if self.projector is None:
            return
        
        self.projector.set_color_temperature_red_offset(offset)

    def set_color_temperature_green_gain(self, gain: int):

        if self.projector is None:
            return
        
        self.projector.set_color_temperature_green_gain(gain)

    def set_color_temperature_green_offset(self, offset: int):

        if self.projector is None:
            return
        
        self.projector.set_color_temperature_green_offset(offset)

    def set_color_temperature_blue_gain(self, gain: int):

        if self.projector is None:
            return
        
        self.projector.set_color_temperature_blue_gain(gain)

    def set_color_temperature_blue_offset(self, offset: int):

        if self.projector is None:
            return
        
        self.projector.set_color_temperature_blue_offset(offset)

    def power_on(self):
        
        if self.projector is None:
            return

        self.projector.power_on()

    def power_off(self):

        if self.projector is None:
            return
        
        self.projector.power_off()

    def get_state(self):
        
        return self.view.get_state()
    
    def stop(self):
        
        self.thread.quit()
        self.thread.wait() 

if __name__ == "__main__":
    
    app = QApplication([])
    window = ProjectorWidget()
    window.show()
    app.exec()
