from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict
import os 

from .tracking_widget import TrackingWidget
from .open_loop_widget import OpenLoopWidget
from .video_recording_widget import VideoOutputWidget
from qt_widgets import LabeledEditLine


class SettingsWidget(QWidget):

    state_changed = pyqtSignal()
    openloop_coords_signal = pyqtSignal()
    CSV_FOLDER: str = 'output/data'

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.create_components()
        self.layout_components()

    def create_components(self):

        self.tracking_widget = TrackingWidget()
        self.open_loop_widget = OpenLoopWidget()
        self.video_recording_widget = VideoOutputWidget()

        self.edt_filename = LabeledEditLine()
        self.edt_filename.setLabel('result file:')
        self.edt_filename.setText(os.path.join(self.CSV_FOLDER, f'{self.fish_id.value():02}_{self.dpf.value():02}dpf_{self.line.text()}.csv'))
        self.edt_filename.textChanged.connect(self.state_changed)

        self.tracking_widget.state_changed.connect(self.state_changed)
        self.open_loop_widget.state_changed.connect(self.state_changed)
        self.open_loop_widget.openloop_coords_signal.connect(self.openloop_coords_signal)
        self.video_recording_widget.state_changed.connect(self.state_changed)

    def force_videorecording(self, force: bool):
        self.video_recording_widget.force_checked(force)

    def set_tracking_visible(self, visible: bool):
        self.tracking_widget.setVisible(visible)

    def set_open_loop_visible(self, visible: bool):
        self.open_loop_widget.setVisible(visible)
        
    def layout_components(self):
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.tracking_widget)
        layout.addWidget(self.open_loop_widget)
        layout.addWidget(self.video_recording_widget)
        layout.addStretch()

    def get_state(self) -> Dict:

        state = {}
        state['tracking'] = self.tracking_widget.get_state()
        state['openloop'] = self.open_loop_widget.get_state()
        state['videorecording'] = self.video_recording_widget.get_state()
        return state
    
    def set_state(self, state: Dict) -> None:
        
        setters = {
            'tracking': self.tracking_widget.set_state,
            'openloop': self.open_loop_widget.set_state,
            'videorecording': self.video_recording_widget.set_state
        }

        for key, setter in setters.items():
            if key in state:
                setter(state[key])