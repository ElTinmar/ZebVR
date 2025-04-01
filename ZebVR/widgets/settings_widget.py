from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict
import os

from .tracking_widget import TrackingWidget
from .video_recording_widget import VideoOutputWidget
from .experiment_data_widget import ExperimentDataWidget
from .stim_output_widget import StimOutputWidget

class SettingsWidget(QWidget):

    state_changed = pyqtSignal()
    OUTPUT_FOLDER: str = 'output/data'

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.prefix = ''
        self.create_components()
        self.layout_components()

    def create_components(self):

        self.experiment_data_widget = ExperimentDataWidget()
        self.tracking_widget = TrackingWidget()
        self.video_recording_widget = VideoOutputWidget()
        self.stim_output_widget = StimOutputWidget()

        self.tracking_widget.state_changed.connect(self.state_changed)
        self.video_recording_widget.state_changed.connect(self.state_changed)

        self.experiment_data_widget.prefix_changed.connect(self.tracking_widget.update_prefix)
        self.experiment_data_widget.prefix_changed.connect(self.video_recording_widget.update_prefix)
        self.experiment_data_widget.prefix_changed.connect(self.stim_output_widget.update_prefix)
        self.experiment_data_widget.prefix_changed.connect(self.update_prefix)
        
        self.experiment_data_widget.experiment_data()

    def update_prefix(self, prefix) -> None:
        self.prefix = os.path.join(self.OUTPUT_FOLDER, prefix)

    def force_videorecording(self, force: bool):
        self.video_recording_widget.force_checked(force)

    def set_tracking_visible(self, visible: bool):
        self.tracking_widget.setVisible(visible)

    def set_stim_output_visible(self, visible: bool):
        self.stim_output_widget.setVisible(visible)
        
    def layout_components(self) -> None:
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.experiment_data_widget)
        layout.addWidget(self.tracking_widget)
        layout.addWidget(self.video_recording_widget)
        layout.addWidget(self.stim_output_widget)
        layout.addStretch()

    def get_state(self) -> Dict:

        state = {}
        state['prefix'] = self.prefix
        state['experiment_data'] = self.experiment_data_widget.get_state()
        state['tracking'] = self.tracking_widget.get_state()
        state['videorecording'] = self.video_recording_widget.get_state()
        state['stim_output'] = self.stim_output_widget.get_state()
        return state
    
    def set_state(self, state: Dict) -> None:
        
        setters = {
            'experiment_data': self.experiment_data_widget.set_state,
            'tracking': self.tracking_widget.set_state,
            'videorecording': self.video_recording_widget.set_state,
            'stim_output': self.stim_output_widget.set_state
        }

        for key, setter in setters.items():
            if key in state:
                setter(state[key])
        
        self.prefix = state.get('prefix', '')