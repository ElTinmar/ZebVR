from dagline import WorkerNode
import time
from numpy.typing import NDArray
from typing import Dict, Optional
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from qt_widgets import LabeledDoubleSpinBox, LabeledSliderDoubleSpinBox

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
        self.window.setWindowTitle('Camera controls')
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
        self.app.sendPostedEvents()
        time.sleep(0.01)

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