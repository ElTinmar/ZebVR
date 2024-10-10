from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout,
    QHBoxLayout,
    QFileDialog,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QGroupBox,
    QStackedWidget
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict
import os

from qt_widgets import LabeledSpinBox, LabeledDoubleSpinBox, LabeledEditLine, LabeledComboBox, FileSaveLabeledEditButton

class OutputWidget(QWidget):

    state_changed = pyqtSignal()
    CSV_FOLDER: str = 'output/data'
    DEFAULT_VIDEOFILE: str = 'default.avi'

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        
        self.filename = ''
        self.declare_components()
        self.layout_components()

    def declare_components(self):
        
        ## data recording -----------------------------------
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

        ## video recording ------------------------------------
        self.video_group = QGroupBox('Enable video recording')
        self.video_group.setCheckable(True)
        self.video_group.setChecked(False)
        self.video_group.toggled.connect(self.state_changed)

        self.video_decimation = LabeledSpinBox()
        self.video_decimation.setText('Frame decimation:')
        self.video_decimation.setRange(1, 10)
        self.video_decimation.setValue(1)
        self.video_decimation.valueChanged.connect(self.state_changed)

        self.video_combobox = LabeledComboBox()
        self.video_combobox.setText('recording format')
        self.video_combobox.addItem('image sequence')
        self.video_combobox.addItem('video file')
        self.video_combobox.currentIndexChanged.connect(self.video_output_changed)

        # image series
        self.image_series = QWidget()

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

        # video         
        self.single_video = QWidget()

        self.video_file = FileSaveLabeledEditButton()
        self.video_file.setLabel('video file:')
        self.video_file.setDefault(self.DEFAULT_VIDEOFILE)
        self.video_file.textChanged.connect(self.state_changed)

        self.use_gpu = QCheckBox('Use gpu:')
        self.use_gpu.setChecked(False)
        self.use_gpu.stateChanged.connect(self.gpu_toggled)

        self.codec_combobox = LabeledComboBox()
        self.codec_combobox.setText('video codec:')
        self.codec_combobox.addItem('libx264')
        self.codec_combobox.addItem('hevc')
        self.codec_combobox.currentIndexChanged.connect(self.state_changed)        

        self.video_preset = LabeledComboBox()
        self.video_preset.setText('video preset:')
        self.video_preset.addItem('p1')
        self.video_preset.addItem('p2')
        self.video_preset.addItem('p3')
        self.video_preset.addItem('p4')
        self.video_preset.addItem('p5')
        self.video_preset.addItem('p6')
        self.video_preset.addItem('p7')
        self.video_preset.currentIndexChanged.connect(self.state_changed)        

        self.video_quality = LabeledSpinBox()
        self.video_quality.setText('Video quality (crf):')
        self.video_quality.setRange(0, 51)
        self.video_quality.setValue(23)
        self.video_quality.valueChanged.connect(self.state_changed)

        # stack
        self.video_stack = QStackedWidget(self)
        self.video_stack.addWidget(self.image_series)
        self.video_stack.addWidget(self.single_video)

        ## logs ------------------------------------------------------
        self.log_group = QGroupBox('Logs')

        self.worker_logfile = LabeledEditLine()
        self.worker_logfile.setLabel('worker log file:')
        self.worker_logfile.setText('workers.log')
        self.worker_logfile.textChanged.connect(self.state_changed)

        self.queue_logfile = LabeledEditLine()
        self.queue_logfile.setLabel('queue log file:')
        self.queue_logfile.setText('queues.log')
        self.queue_logfile.textChanged.connect(self.state_changed)

    def layout_components(self):
        
        select_video = QHBoxLayout()
        select_video.addWidget(self.video_recording_button)
        select_video.addWidget(self.video_recording_dir)

        image_series_layout = QVBoxLayout(self.image_series)
        image_series_layout.addLayout(select_video)
        image_series_layout.addWidget(self.video_recording_compress)
        image_series_layout.addWidget(self.video_recording_resize)
        image_series_layout.addStretch()

        single_video_layout = QVBoxLayout(self.single_video)
        single_video_layout.addWidget(self.video_file)
        single_video_layout.addWidget(self.use_gpu)
        single_video_layout.addWidget(self.codec_combobox)
        single_video_layout.addWidget(self.video_preset)
        single_video_layout.addWidget(self.video_quality)
        single_video_layout.addStretch()

        video_layout = QVBoxLayout()
        video_layout.addWidget(self.video_decimation)
        video_layout.addWidget(self.video_combobox)
        video_layout.addWidget(self.video_stack)
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

    def gpu_toggled(self):

        if self.use_gpu.isChecked():
            self.codec_combobox.clear()
            self.codec_combobox.addItem('h264_nvenc')
            self.codec_combobox.addItem('hevc_nvenc')

        else:
            self.codec_combobox.clear()
            self.codec_combobox.addItem('libx264')
            self.codec_combobox.addItem('hevc')

    def video_output_changed(self, index: int):
        self.video_stack.setCurrentIndex(index)
        self.state_changed.emit()

    def enable_video_recording(self, isChecked: bool):
        self.video_group.setChecked(isChecked)

    def experiment_data(self):
        self.filename = os.path.join(self.CSV_FOLDER, f'{self.fish_id.value():02}_{self.dpf.value():02}dpf.csv')
        self.edt_filename.setText(self.filename)
        self.state_changed.emit()

    def select_video_dir(self):
        filename = QFileDialog.getExistingDirectory(self, "Select Directory")
        self.video_recording_dir.setText(filename)

    def get_state(self) -> Dict:
        state = {}
        state['fish_id'] = self.fish_id.value()
        state['dpf'] = self.dpf.value()
        state['csv_filename'] = self.edt_filename.text()
        state['video_recording'] = self.video_group.isChecked()
        state['video_recording_dir'] = self.video_recording_dir.text()
        state['video_recording_compression'] = self.video_recording_compress.isChecked()
        state['video_recording_resize'] = self.video_recording_resize.value()
        state['video_decimation'] = self.video_decimation.value()
        state['video_filename'] = self.video_file.text()
        state['video_codec'] = self.codec_combobox.currentText()
        state['video_gpu'] = self.use_gpu.isChecked()
        state['video_preset'] = self.video_preset.currentText()
        state['video_quality'] = self.video_quality.value()
        state['worker_logfile'] = self.worker_logfile.text()
        state['queue_logfile'] = self.queue_logfile.text()
        return state
    
    def set_state(self, state: Dict) -> None:
        try:
            self.fish_id.setValue(state['fish_id'])
            self.dpf.setValue(state['dpf'])
            self.edt_filename.setText(state['csv_filename'])
            self.video_group.setChecked(state['video_recording'])
            self.video_recording_dir.setText(state['video_recording_dir'])
            self.video_recording_compress.setChecked(state['video_recording_compression'])
            self.video_recording_resize.setValue(state['video_recording_resize'])
            self.video_decimation.setValue(state['video_decimation'])
            self.video_file.setText(state['video_filename'])
            self.codec_combobox.setCurrentText(state['video_codec'])
            self.use_gpu.setChecked(state['video_gpu'])
            self.video_preset.setCurrentText(state['video_preset'])
            self.video_quality.setValue(state['video_quality'])
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
