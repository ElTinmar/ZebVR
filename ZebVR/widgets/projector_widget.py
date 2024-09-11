from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFileDialog, QCheckBox
from PyQt5.QtCore import pyqtSignal
from typing import Dict

from qt_widgets import LabeledDoubleSpinBox, LabeledSpinBox, NDarray_to_QPixmap

class ProjectorWidget(QWidget):

    state_changed = pyqtSignal()

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

        self.scale_y = LabeledDoubleSpinBox()
        self.scale_y.setText('scale Y:')
        self.scale_y.setValue(1.0)
        self.scale_y.setSingleStep(0.05)
        self.scale_y.valueChanged.connect(self.state_changed.emit)

        # Serial communication with the projector
        self.power_on = QPushButton('Power On')
        self.power_off = QPushButton('Power Off')
        self.video_source = QComboBox()
        self.fast_input_mode = QCheckBox('Fast input mode')

        self.serial_number = QLabel('S/N:') 
        self.power_status = QLabel('Power:')
        self.input_mode = QLabel('Input Source:')
        self.temperature = QLabel(u'Temperature (\N{DEGREE SIGN}C)')

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
        main_layout.addWidget(QLabel('')) # empty label just for spacing
        main_layout.addLayout(power_layout)
        main_layout.addWidget(self.video_source)
        main_layout.addWidget(self.fast_input_mode)
        main_layout.addWidget(self.serial_number)
        main_layout.addWidget(self.power_status)
        main_layout.addWidget(self.input_mode)
        main_layout.addWidget(self.temperature)
        main_layout.addStretch()

    def get_state(self) -> Dict:
        state = {}
        state['resolution'] = (self.proj_width.value(), self.proj_height.value())
        state['offset'] = (self.offset_x.value(), self.offset_y.value())
        state['pixel_scale'] = (self.scale_x.value(), self.scale_y.value())
        state['fps'] = self.proj_fps.value()
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
