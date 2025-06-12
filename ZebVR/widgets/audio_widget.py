from PyQt5.QtWidgets import (
    QApplication, 
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLabel, 
    QPushButton, 
    QComboBox, 
    QCheckBox,
)
from typing import Dict
import sounddevice as sd

# TODO finish that

class AudioWidget(QWidget):

    def __init__(self,*args,**kwargs):

        super().__init__(*args, **kwargs)
        self.declare_components()
        self.layout_components()   

    def declare_components(self) -> None:
        self.device_combo = QComboBox()
        self.channels_spinbox = QSpinBox()
        self.sample_rate_spinbox = QSpinBox()
        self.recording_checkbox = QCheckBox("Recording")
        
        # Populate device combo box with available audio devices
        devices = sd.query_devices()
        for device in devices:
            self.device_combo.addItem(device['name'])
        
        # Set default values for channels and sample rate
        self.channels_spinbox.setRange(1, 8)
        self.channels_spinbox.setValue(2)
        self.sample_rate_spinbox.setRange(8000, 192000)
        self.sample_rate_spinbox.setValue(44100)
        self.declare_components()
        self.layout_components()
        self.setWindowTitle('Audio Settings')            

    def layout_components(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.main_layout.addWidget(QLabel("Device:"))
        self.main_layout.addWidget(self.device_combo)
        self.main_layout.addWidget(QLabel("Channels:"))
        self.main_layout.addWidget(self.channels_spinbox)
        self.main_layout.addWidget(QLabel("Sample Rate:"))
        self.main_layout.addWidget(self.sample_rate_spinbox)
        self.main_layout.addWidget(self.recording_checkbox)

    def set_state(self, state: Dict):
        self.device_combo.setCurrentText(state.get('device', ''))
        self.channels_spinbox.setValue(state.get('channels', 1))
        self.sample_rate_spinbox.setValue(state.get('sample_rate', 44100))
        self.recording_checkbox.setChecked(state.get('recording', False))

    def get_state(self):
        state = {}
        state['device'] = self.device_combo.currentText()
        state['channels'] = self.channels_spinbox.value()
        state['sample_rate'] = self.sample_rate_spinbox.value()
        state['recording'] = self.recording_checkbox.isChecked()
        return state

if __name__ == "__main__":
    
    app = QApplication([])
    window = AudioWidget()
    window.show()
    app.exec()
