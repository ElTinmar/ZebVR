from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict
from qt_widgets import LabeledSpinBox
from .log_output_widget import LogOutputWidget

# TODO add loglevel to choose for each log

class LogsWidget(QWidget):

    state_changed = pyqtSignal()

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.create_components()
        self.layout_components()

    def create_components(self):

        self.log_widget = LogOutputWidget()
        self.log_widget.state_changed.connect(self.state_changed)

        self.queue_refresh_time_microsec = LabeledSpinBox()
        self.queue_refresh_time_microsec.setText(u'queue refresh time (\N{GREEK SMALL LETTER MU}s):')
        self.queue_refresh_time_microsec.setRange(1,100_000)
        self.queue_refresh_time_microsec.setValue(100)
        self.queue_refresh_time_microsec.valueChanged.connect(self.state_changed)
        
    def layout_components(self):
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.log_widget)
        layout.addWidget(self.queue_refresh_time_microsec)
        layout.addStretch()

    def get_state(self) -> Dict:

        state = {}
        state['log'] = self.log_widget.get_state()
        state['queue_refresh_time_microsec'] = self.queue_refresh_time_microsec.value()
        return state
    
    def set_state(self, state: Dict) -> None:

        setters = {
            'log': self.log_widget.set_state,
            'queue_refresh_time_microsec': self.queue_refresh_time_microsec.setValue,
        }

        for key, setter in setters.items():
            if key in state:
                setter(state[key])

        