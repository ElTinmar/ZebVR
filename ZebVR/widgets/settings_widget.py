from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict
from qt_widgets import LabeledSpinBox

from .tracking_widget import TrackingWidget
from .open_loop_widget import OpenLoopWidget
from .video_recording_widget import VideoOutputWidget
from .log_output_widget import LogOutputWidget

class SettingsWidget(QWidget):

    state_changed = pyqtSignal()

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.create_components()
        self.layout_components()

    def create_components(self):

        self.tracking_widget = TrackingWidget()
        self.open_loop_widget = OpenLoopWidget()
        self.video_recording_widget = VideoOutputWidget()
        self.log_widget = LogOutputWidget()

        self.tracking_widget.state_changed.connect(self.state_changed)
        self.open_loop_widget.state_changed.connect(self.state_changed)
        self.video_recording_widget.state_changed.connect(self.state_changed)
        self.log_widget.state_changed.connect(self.state_changed)

        self.queue_refresh_time_microsec = LabeledSpinBox()
        self.queue_refresh_time_microsec.setText(u'queue refresh time (\N{GREEK SMALL LETTER MU}s):')
        self.queue_refresh_time_microsec.setRange(1,100_000)
        self.queue_refresh_time_microsec.setValue(100)
        self.queue_refresh_time_microsec.valueChanged.connect(self.state_changed)

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
        layout.addWidget(self.log_widget)
        layout.addWidget(self.queue_refresh_time_microsec)
        layout.addStretch()

    def get_state(self) -> Dict:

        state = {}
        state['tracking'] = self.tracking_widget.get_state()
        state['openloop'] = self.open_loop_widget.get_state()
        state['videorecording'] = self.video_recording_widget.get_state()
        state['log'] = self.log_widget.get_state()
        state['queue_refresh_time_microsec'] = self.queue_refresh_time_microsec.value()
        return state
    
    def set_state(self, state: Dict) -> None:

        try:
            self.tracking_widget.set_state(state['tracking'])
            self.open_loop_widget.set_state(state['openloop'])
            self.video_recording_widget.set_state(state['videorecording'])
            self.log_widget.set_state(state['log'])
            self.queue_refresh_time_microsec.setValue(state['queue_refresh_time_microsec'])

        except KeyError:
            print('Wrong state keys provided to Settings widget')
            raise