
from PyQt5.QtWidgets import (
    QWidget, 
    QApplication,
    QVBoxLayout,
    QGroupBox,
    QCheckBox
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict
import os

from qt_widgets import LabeledSpinBox, FileOpenLabeledEditButton, LabeledEditLine

class TrackingWidget(QWidget):

    state_changed = pyqtSignal()
    CSV_FOLDER: str = 'output/data'
    DEFAULT_TRACKING_FILE =  'ZebVR/default/tracking.json'

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.filename = ''
        self.declare_components()
        self.layout_components()

    def declare_components(self):

        self.closedloop_group = QGroupBox('tracking settings')

        self.background_gpu = QCheckBox('GPU background subtraction')
        self.background_gpu.setChecked(True)
        self.background_gpu.stateChanged.connect(self.state_changed)

        self.n_tail_pts_interp = LabeledSpinBox()
        self.n_tail_pts_interp.setText('# tail points interp:')
        self.n_tail_pts_interp.setValue(40)
        self.n_tail_pts_interp.valueChanged.connect(self.state_changed)

        self.tracking_settings = FileOpenLabeledEditButton()
        self.tracking_settings.setLabel('tracker settings file:')
        self.tracking_settings.setDefault(self.DEFAULT_TRACKING_FILE)
        self.tracking_settings.textChanged.connect(self.state_changed)

        self.display_fps = LabeledSpinBox()
        self.display_fps.setText('FPS display:')
        self.display_fps.setValue(30)
        self.display_fps.valueChanged.connect(self.state_changed)

        self.edt_filename = LabeledEditLine()
        self.edt_filename.setLabel('result file:')
        self.edt_filename.setText('tracking.csv')
        self.edt_filename.textChanged.connect(self.state_changed)

    def update_prefix(self, prefix: str):

        self.filename = os.path.join(self.CSV_FOLDER, f'tracking_{prefix}.csv')
        self.edt_filename.setText(self.filename)
        self.state_changed.emit()

    def layout_components(self):

        closedloop_layout = QVBoxLayout()
        closedloop_layout.addWidget(self.tracking_settings)
        closedloop_layout.addWidget(self.background_gpu)
        closedloop_layout.addWidget(self.n_tail_pts_interp)
        closedloop_layout.addWidget(self.display_fps)
        closedloop_layout.addWidget(self.edt_filename)
        self.closedloop_group.setLayout(closedloop_layout)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.closedloop_group)

    def get_state(self) -> Dict:

        state = {}
        state['tracker_settings_file'] = self.tracking_settings.text()
        state['background_gpu'] = self.background_gpu.isChecked()
        state['n_tail_pts_interp'] = self.n_tail_pts_interp.value()
        state['display_fps'] = self.display_fps.value()
        state['csv_filename'] = self.edt_filename.text()
        return state
    
    def set_state(self, state: Dict) -> None:

        setters = {
            'tracker_settings_file': self.tracking_settings.setText,
            'background_gpu': self.background_gpu.setChecked,
            'n_tail_pts_interp': self.n_tail_pts_interp.setValue,
            'display_fps': self.display_fps.setValue,
            'csv_filename': self.edt_filename.setText
        }
        
        for key, setter in setters.items():
            if key in state:
                setter(state[key])

if __name__ == "__main__":
    
    app = QApplication([])
    window = TrackingWidget()
    window.show()
    app.exec()
