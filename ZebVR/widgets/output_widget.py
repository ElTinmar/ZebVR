from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QGroupBox,
    QLabel
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict
import os

from qt_widgets import LabeledSpinBox, LabeledDoubleSpinBox, LabeledEditLine

class OutputWidget(QWidget):

    state_changed = pyqtSignal()
    CSV_FOLDER = 'output/data'

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        
        self.filename = ''
        self.declare_components()
        self.layout_components()

    def declare_components(self):
        
        # data recording
        self.data_group = QGroupBox('Data')
    
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

        # video recording
        self.video_group = QGroupBox('Enable video recording')
        self.video_group.setCheckable(True)
        self.video_group.setChecked(False)
        self.video_group.toggled.connect(self.state_changed)

        self.video_recording_button = QPushButton('Video directory') 
        self.video_recording_button.clicked.connect(self.select_video_dir)

        self.video_recording_dir = QLineEdit()
        self.video_recording_dir.setText('')
        self.video_recording_dir.textChanged.connect(self.state_changed)

        self.video_recording_compress = QCheckBox('Compress')
        self.video_recording_compress.setChecked(True)
        self.video_recording_compress.stateChanged.connect(self.state_changed)

        self.video_recording_resize = LabeledDoubleSpinBox()
        self.video_recording_resize.setText('Resize video:')
        self.video_recording_resize.setRange(0,1)
        self.video_recording_resize.setSingleStep(0.05)
        self.video_recording_resize.setValue(0.25)
        self.video_recording_resize.valueChanged.connect(self.state_changed)

        self.video_recording_fps = LabeledSpinBox()
        self.video_recording_fps.setText('FPS Recording:')
        self.video_recording_fps.setRange(0, 1_000)
        self.video_recording_fps.setValue(20)
        self.video_recording_fps.valueChanged.connect(self.state_changed)

        # logs
        self.log_group = QGroupBox('Logs')

        self.worker_logfile = LabeledEditLine()
        self.worker_logfile.setLabel('worker log file:')
        self.worker_logfile.setText('workers.log')
        self.worker_logfile.textChanged.connect(self.state_changed)

        self.queue_logfile = LabeledEditLine()
        self.queue_logfile.setLabel('queue log file:')
        self.queue_logfile.setText('queues.log')
        self.queue_logfile.textChanged.connect(self.state_changed)

    def experiment_data(self):
        self.filename = os.path.join(self.CSV_FOLDER, f'{self.fish_id.value():02}_{self.dpf.value():02}dpf.csv')
        self.edt_filename.setText(self.filename)
        self.state_changed.emit()

    def select_video_dir(self):
        filename = QFileDialog.getExistingDirectory(self, "Select Directory")
        self.video_recording_dir.setText(filename)

    def layout_components(self):
        
        select_video = QHBoxLayout()
        select_video.addWidget(self.video_recording_button)
        select_video.addWidget(self.video_recording_dir)

        video_layout = QVBoxLayout()
        video_layout.addLayout(select_video)
        video_layout.addWidget(self.video_recording_compress)
        video_layout.addWidget(self.video_recording_resize)
        video_layout.addWidget(self.video_recording_fps)
        self.video_group.setLayout(video_layout)

        data_layout = QVBoxLayout()
        data_layout.addWidget(self.fish_id)
        data_layout.addWidget(self.dpf)
        data_layout.addWidget(self.edt_filename)
        self.data_group.setLayout(data_layout)

        log_layout = QVBoxLayout()
        log_layout.addWidget(self.worker_logfile)
        log_layout.addWidget(self.queue_logfile)
        self.log_group.setLayout(log_layout)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.data_group)
        main_layout.addSpacing(20) 
        main_layout.addWidget(self.video_group)
        main_layout.addSpacing(20) 
        main_layout.addWidget(self.log_group)
        main_layout.addStretch()

    def get_state(self) -> Dict:
        state = {}
        state['fish_id'] = self.fish_id.value()
        state['dpf'] = self.dpf.value()
        state['csv_filename'] = self.edt_filename.text()
        state['video_recording'] = self.video_group.isChecked()
        state['video_recording_dir'] = self.video_recording_dir.text()
        state['video_recording_compression'] = self.video_recording_compress.isChecked()
        state['video_recording_resize'] = self.video_recording_resize.value()
        state['video_recording_fps'] = self.video_recording_fps.value()
        state['worker_logfile'] = self.worker_logfile.text()
        state['queue_logfile'] = self.queue_logfile.text()
        return state
    
    def set_state(self, state: Dict) -> None:
        try:
            self.fish_id.setValue(state['fish_id'])
            self.fish_id.setValue(state['dpf'])
            self.edt_filename.setText(state['csv_filename'])
            self.video_group.setChecked(state['video_recording'])
            self.video_recording_dir.setText(state['video_recording_dir'])
            self.video_recording_compress.setChecked(state['video_recording_compression'])
            self.video_recording_resize.setValue(state['video_recording_resize'])
            self.video_recording_fps.setValue(state['video_recording_fps'])
            self.worker_logfile.setText(state['worker_logfile'])
            self.queue_logfile.setText(state['queue_logfile'])

        except KeyError:
            print('Wrong state keys provided to output widget')
            raise

if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication, QMainWindow
    from PyQt5.QtCore import  QRunnable, QThreadPool

    class Window(QMainWindow):

        def __init__(self,*args,**kwargs):

            super().__init__(*args, **kwargs)
            self.output_widget = OutputWidget()
            self.setCentralWidget(self.output_widget)
            self.output_widget.state_changed.connect(self.state_changed)

        def state_changed(self):
            print(self.output_widget.get_state())
    
    app = QApplication([])
    window = Window()
    window.show()
    app.exec()
