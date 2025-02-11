
from PyQt5.QtWidgets import (
    QWidget, 
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
    
        self.n_background_workers = LabeledSpinBox()
        self.n_background_workers.setText('# background subtraction workers:')
        self.n_background_workers.setValue(1)
        self.n_background_workers.valueChanged.connect(self.state_changed)

        self.background_gpu = QCheckBox('GPU background subtraction')
        self.background_gpu.setChecked(True)
        self.background_gpu.stateChanged.connect(self.state_changed)
    
        self.n_tracker_workers = LabeledSpinBox()
        self.n_tracker_workers.setText('# tracker workers:')
        self.n_tracker_workers.setValue(1)
        self.n_tracker_workers.valueChanged.connect(self.state_changed)

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

                
        ## data recording -----------------------------------
        self.data_group = QGroupBox('tracking output')
    
        self.fish_id = LabeledSpinBox()
        self.fish_id.setText('Fish ID:')
        self.fish_id.setValue(0)
        self.fish_id.valueChanged.connect(self.experiment_data)

        self.dpf = LabeledSpinBox()
        self.dpf.setText('Fish age (dpf):')
        self.dpf.setValue(7)
        self.dpf.valueChanged.connect(self.experiment_data)

        self.edt_filename = LabeledEditLine()
        self.edt_filename.setLabel('result file:')
        self.edt_filename.setText(os.path.join(self.CSV_FOLDER, f'{self.fish_id.value():02}_{self.dpf.value():02}dpf.csv'))
        self.edt_filename.textChanged.connect(self.state_changed)

    def layout_components(self):

        closedloop_layout = QVBoxLayout()
        closedloop_layout.addWidget(self.background_gpu)
        closedloop_layout.addWidget(self.n_background_workers)
        closedloop_layout.addWidget(self.n_tracker_workers)
        closedloop_layout.addWidget(self.n_tail_pts_interp)
        closedloop_layout.addWidget(self.display_fps)
        closedloop_layout.addWidget(self.tracking_settings)
        self.closedloop_group.setLayout(closedloop_layout)

        data_layout = QVBoxLayout()
        data_layout.addWidget(self.fish_id)
        data_layout.addWidget(self.dpf)
        data_layout.addWidget(self.edt_filename)
        self.data_group.setLayout(data_layout)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.closedloop_group)
        main_layout.addWidget(self.data_group)

    def experiment_data(self):
        self.filename = os.path.join(self.CSV_FOLDER, f'{self.fish_id.value():02}_{self.dpf.value():02}dpf.csv')
        self.edt_filename.setText(self.filename)
        self.state_changed.emit()

    def get_state(self) -> Dict:

        state = {}
        state['tracking_file'] = self.tracking_settings.text()
        state['n_background_workers'] = self.n_background_workers.value()
        state['n_tracker_workers'] = self.n_tracker_workers.value()
        state['background_gpu'] = self.background_gpu.isChecked()
        state['n_tail_pts_interp'] = self.n_tail_pts_interp.value()
        state['display_fps'] = self.display_fps.value()
        state['fish_id'] = self.fish_id.value()
        state['dpf'] = self.dpf.value()
        state['csv_filename'] = self.edt_filename.text()
        return state
    
    def set_state(self, state: Dict) -> None:

        try:
            self.tracking_settings.setText(state['tracking_file'])
            self.heading = state['heading']
            self.n_background_workers.setValue(state['n_background_workers'])
            self.n_tracker_workers.setValue(state['n_tracker_workers'])
            self.background_gpu.setChecked(state['background_gpu'])
            self.n_tail_pts_interp.setValue(state['n_tail_pts_interp'])
            self.display_fps.setValue(state['display_fps'])
            self.fish_id.setValue(state['fish_id'])
            self.dpf.setValue(state['dpf'])
            self.edt_filename.setText(state['csv_filename'])

        except KeyError:
            print('Wrong state keys provided to VR setting widget')
            raise

if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication, QMainWindow

    class Window(QMainWindow):

        def __init__(self,*args,**kwargs):

            super().__init__(*args, **kwargs)
            self.closeloop_widget = CloseLoopWidget()
            self.setCentralWidget(self.closeloop_widget)
            self.closeloop_widget.state_changed.connect(self.state_changed)

        def state_changed(self):
            print(self.closeloop_widget.get_state())

        def openloop(self):
            print('openloop coords clicked')
    
    app = QApplication([])
    window = Window()
    window.show()
    app.exec()
