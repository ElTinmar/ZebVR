from typing import Dict
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from qt_widgets import LabeledDoubleSpinBox, LabeledSliderDoubleSpinBox

# TODO populate with sane values on startup
class CameraWidget(QWidget):

    def __init__(self,*args,**kwargs):

        super().__init__(*args, **kwargs)

        self.updated = False
        self.controls = [
            'framerate', 
            'exposure', 
            'gain', 
        ]
        self.declare_components()
        self.layout_components()
        self.setWindowTitle('Camera controls')

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

        layout_controls = QVBoxLayout(self)
        layout_controls.addStretch()
        layout_controls.addWidget(self.exposure_spinbox)
        layout_controls.addWidget(self.gain_spinbox)
        layout_controls.addWidget(self.framerate_spinbox)
        layout_controls.addStretch()

    def on_change(self):
        self.updated = True

    def block_signals(self, block):
        for widget in self.findChildren(QWidget):
            widget.blockSignals(block)

    def is_updated(self) -> bool:
        return self.updated
    
    def set_updated(self, updated:bool) -> None:
        self.updated = updated

    def get_state(self) -> Dict:
        state = {}
        for c in self.controls:
            spinbox = getattr(self, c + '_spinbox')
            state[c] = spinbox.value()
        return state
    