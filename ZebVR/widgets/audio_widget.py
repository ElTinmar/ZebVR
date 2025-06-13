from PyQt5.QtWidgets import (
    QApplication, 
    QWidget, 
    QVBoxLayout, 
    QCheckBox,
)
from PyQt5.QtCore import pyqtSignal
from qt_widgets import LabeledComboBox, LabeledSpinBox, NDarray_to_QPixmap

from typing import Dict
import sounddevice as sd

class AudioWidget(QWidget):

    state_changed = pyqtSignal()

    def __init__(self,*args,**kwargs):

        super().__init__(*args, **kwargs)
        self.output_devices = [device for device in sd.query_devices() if device['max_output_channels'] > 0]
        self.declare_components()
        self.layout_components()   
        self.enable_audio()

    def declare_components(self) -> None:
        
        self.enabled_checkbox = QCheckBox("enabled")
        self.enabled_checkbox.setChecked(False)
        self.enabled_checkbox.stateChanged.connect(self.enable_audio)

        self.device_combo = LabeledComboBox()
        self.device_combo.setText('output device')
        self.device_combo.addItems([device['name'] for device in self.output_devices])
        self.device_combo.currentIndexChanged.connect(self.device_changed)

        self.channels_spinbox = LabeledSpinBox()
        self.channels_spinbox.setText('channels')
        self.channels_spinbox.setRange(1, self.output_devices[0]['max_output_channels'])
        self.channels_spinbox.setValue(self.output_devices[0]['max_output_channels'])
        self.channels_spinbox.valueChanged.connect(self.state_changed)
    
        self.samplerate_spinbox = LabeledSpinBox()
        self.samplerate_spinbox.setText('samplerate')
        self.samplerate_spinbox.setRange(8000, 192_000)
        self.samplerate_spinbox.setValue(self.output_devices[0]['default_samplerate'])
        self.samplerate_spinbox.setEnabled(False)

    def enable_audio(self) -> None:

        if self.enabled_checkbox.isChecked():
            self.device_combo.setEnabled(True)
            self.channels_spinbox.setEnabled(True)
        else:
            self.device_combo.setEnabled(False)
            self.channels_spinbox.setEnabled(False)

        self.state_changed.emit()

    def device_changed(self) -> None:

        dev = self.output_devices[self.device_combo.currentIndex()]
        
        max_channels = dev['max_output_channels']
        samplerate = dev['default_samplerate']
        self.channels_spinbox.setRange(1, max_channels)
        self.channels_spinbox.setValue(max_channels)
        self.samplerate_spinbox.setValue(samplerate)

        sd.check_output_settings(
            device = dev['index'], 
            channels = self.channels_spinbox.value(), 
            dtype = 'float32', 
            samplerate = samplerate
        )
        self.state_changed.emit()

    def layout_components(self) -> None:

        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(self.enabled_checkbox)
        self.main_layout.addWidget(self.device_combo)
        self.main_layout.addWidget(self.channels_spinbox)
        self.main_layout.addWidget(self.samplerate_spinbox)
        self.main_layout.addStretch()

    def set_state(self, state: Dict):
        self.device_combo.setCurrentIndex(state.get('index', 0))
        self.channels_spinbox.setValue(state.get('channels', self.output_devices[0][['max_output_channels']]))
        self.enabled_checkbox.setChecked(state.get('enabled', True))
        self.samplerate_spinbox.setValue(state.get('samplerate', self.output_devices[0][['default_samplerate']]))

    def get_state(self):
        state = {}
        state['index'] = self.device_combo.currentIndex()
        state['device_index'] = self.output_devices[self.device_combo.currentIndex()]['index']
        state['channels'] = self.channels_spinbox.value()
        state['samplerate'] = self.samplerate_spinbox.value()
        state['enabled'] = self.enabled_checkbox.isChecked()
        return state

if __name__ == "__main__":
    
    app = QApplication([])
    window = AudioWidget()
    window.show()
    app.exec()
