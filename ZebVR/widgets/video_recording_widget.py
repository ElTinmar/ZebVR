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
from pathlib import Path

from qt_widgets import LabeledSpinBox, LabeledDoubleSpinBox, LabeledComboBox, FileSaveLabeledEditButton

class VideoOutputWidget(QWidget):

    state_changed = pyqtSignal()
    DEFAULT_VIDEOFILE: str = 'video.mp4'
    VIDEO_FOLDER: Path = Path('output/video')

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        
        self.declare_components()
        self.layout_components()

    def declare_components(self) -> None:
        
        ## video recording ------------------------------------
        self.video_group = QGroupBox('Enable video recording')
        self.video_group.setCheckable(True)
        self.video_group.setChecked(False)
        self.video_group.toggled.connect(self.state_changed)

        self.display_fps = LabeledSpinBox()
        self.display_fps.setText('FPS display:')
        self.display_fps.setValue(30)
        self.display_fps.valueChanged.connect(self.state_changed)

        self.video_decimation = LabeledSpinBox()
        self.video_decimation.setText('Frame decimation:')
        self.video_decimation.setRange(1, 10)
        self.video_decimation.setValue(1)
        self.video_decimation.valueChanged.connect(self.state_changed)

        self.video_combobox = LabeledComboBox()
        self.video_combobox.setText('recording format')
        self.video_combobox.addItem('video file')
        self.video_combobox.addItem('image sequence')
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

        self.use_gpu = QCheckBox('GPU')
        self.use_gpu.setChecked(False)
        self.use_gpu.stateChanged.connect(self.gpu_toggled)

        self.grayscale = QCheckBox('Grayscale')
        self.grayscale.setChecked(False)
        self.grayscale.stateChanged.connect(self.grayscale_toggled)

        self.codec_combobox = LabeledComboBox()
        self.codec_combobox.setText('video codec:')
        self.codec_combobox.addItem('h264')
        self.codec_combobox.addItem('mjpeg')
        self.codec_combobox.addItem('hevc')
        self.codec_combobox.currentIndexChanged.connect(self.codec_changed)        

        self.video_preset = LabeledComboBox()
        self.video_preset.setText('video preset:')
        self.video_preset.addItem('ultrafast')
        self.video_preset.addItem('superfast')
        self.video_preset.addItem('veryfast')
        self.video_preset.addItem('faster')
        self.video_preset.addItem('fast')
        self.video_preset.addItem('medium')
        self.video_preset.addItem('slow')
        self.video_preset.addItem('slower')
        self.video_preset.addItem('veryslow')
        self.video_preset.currentIndexChanged.connect(self.state_changed)        

        self.video_quality = LabeledSpinBox()
        self.video_quality.setText('Video quality (crf):')
        self.video_quality.setRange(-12, 51)
        self.video_quality.setValue(23)
        self.video_quality.valueChanged.connect(self.state_changed)

        # stack
        self.video_stack = QStackedWidget(self)
        self.video_stack.addWidget(self.single_video)
        self.video_stack.addWidget(self.image_series)

    def update_prefix(self, prefix: str) -> None:
        filename = self.VIDEO_FOLDER / f'{prefix}.mp4'
        self.video_file.setText(str(filename))
        self.state_changed.emit()

    def force_checked(self, checked: bool):
        self.video_group.setCheckable(not checked) 
        self.video_group.setChecked(checked)

    def layout_components(self) -> None:
        
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
        single_video_layout.addWidget(self.grayscale)
        single_video_layout.addWidget(self.codec_combobox)
        single_video_layout.addWidget(self.video_preset)
        single_video_layout.addWidget(self.video_quality)
        single_video_layout.addStretch()

        video_layout = QVBoxLayout()
        video_layout.addWidget(self.video_decimation)
        video_layout.addWidget(self.display_fps)
        video_layout.addWidget(self.video_combobox)
        video_layout.addWidget(self.video_stack)
        self.video_group.setLayout(video_layout)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.video_group)

    def codec_changed(self):
        
        if self.codec_combobox.currentText() == 'h264':
            self.video_quality.setRange(-12, 51)
            self.video_quality.setValue(23)
            self.video_preset.setEnabled(True)
        
        elif self.codec_combobox.currentText() == 'hevc':
            self.video_quality.setRange(0, 51)
            self.video_quality.setValue(28)
            self.video_preset.setEnabled(True)
        
        elif self.codec_combobox.currentText() == 'mjpeg':
            self.video_quality.setRange(2, 31)
            self.video_quality.setValue(2)
            self.video_preset.setEnabled(False)

        elif self.codec_combobox.currentText() == 'h264_nvenc':
            self.video_quality.setRange(0, 51)
            self.video_quality.setValue(0)
            self.video_preset.setEnabled(True)

        elif self.codec_combobox.currentText() == 'hevc_nvenc':
            self.video_quality.setRange(0, 51)
            self.video_quality.setValue(0)
            self.video_preset.setEnabled(True)

        self.state_changed.emit()

    def gpu_toggled(self):

        if self.use_gpu.isChecked():

            self.grayscale.setChecked(False)

            self.codec_combobox.clear()
            self.codec_combobox.addItem('h264_nvenc')
            self.codec_combobox.addItem('hevc_nvenc')

            self.video_preset.clear()
            self.video_preset.addItem('p1')
            self.video_preset.addItem('p2')
            self.video_preset.addItem('p3')
            self.video_preset.addItem('p4')
            self.video_preset.addItem('p5')
            self.video_preset.addItem('p6')
            self.video_preset.addItem('p7')

        else:
            self.codec_combobox.clear()
            self.codec_combobox.addItem('h264')
            self.codec_combobox.addItem('mjpeg')
            self.codec_combobox.addItem('hevc')

            self.video_preset.clear()
            self.video_preset.addItem('ultrafast')
            self.video_preset.addItem('superfast')
            self.video_preset.addItem('veryfast')
            self.video_preset.addItem('faster')
            self.video_preset.addItem('fast')
            self.video_preset.addItem('medium')
            self.video_preset.addItem('slow')
            self.video_preset.addItem('slower')
            self.video_preset.addItem('veryslow')
        
        self.state_changed.emit()

    def grayscale_toggled(self):

        if self.grayscale.isChecked():

            self.use_gpu.setChecked(False)

            self.codec_combobox.clear()
            self.codec_combobox.addItem('h264')

            self.video_preset.clear()
            self.video_preset.addItem('ultrafast')
            self.video_preset.addItem('superfast')
            self.video_preset.addItem('veryfast')
            self.video_preset.addItem('faster')
            self.video_preset.addItem('fast')
            self.video_preset.addItem('medium')
            self.video_preset.addItem('slow')
            self.video_preset.addItem('slower')
            self.video_preset.addItem('veryslow')

        else:
            self.codec_combobox.clear()
            self.codec_combobox.addItem('h264')
            self.codec_combobox.addItem('mjpeg')
            self.codec_combobox.addItem('hevc')

            self.video_preset.clear()
            self.video_preset.addItem('ultrafast')
            self.video_preset.addItem('superfast')
            self.video_preset.addItem('veryfast')
            self.video_preset.addItem('faster')
            self.video_preset.addItem('fast')
            self.video_preset.addItem('medium')
            self.video_preset.addItem('slow')
            self.video_preset.addItem('slower')
            self.video_preset.addItem('veryslow')
        
        self.state_changed.emit()

    def video_output_changed(self, index: int):
        self.video_stack.setCurrentIndex(index)
        self.state_changed.emit()

    def enable_video_recording(self, isChecked: bool):
        self.video_group.setChecked(isChecked)

    def select_video_dir(self):
        filename = QFileDialog.getExistingDirectory(self, "Select Directory")
        self.video_recording_dir.setText(filename)

    def get_state(self) -> Dict:
        state = {}
        state['video_recording'] = self.video_group.isChecked()
        state['video_method'] = self.video_combobox.currentText()
        state['video_recording_dir'] = self.video_recording_dir.text()
        state['video_recording_compression'] = self.video_recording_compress.isChecked()
        state['video_recording_resize'] = self.video_recording_resize.value()
        state['video_decimation'] = self.video_decimation.value()
        state['video_filename'] = self.video_file.text()
        state['video_codec'] = self.codec_combobox.currentText()
        state['video_gpu'] = self.use_gpu.isChecked()
        state['video_grayscale'] = self.grayscale.isChecked()
        state['video_preset'] = self.video_preset.currentText()
        state['video_quality'] = self.video_quality.value()
        state['display_fps'] = self.display_fps.value()
        return state
    
    def set_state(self, state: Dict) -> None:
        
        setters = {
            'video_recording': self.video_group.setChecked,
            'video_method': self.video_combobox.setCurrentText,
            'video_recording_dir': self.video_recording_dir.setText,
            'video_recording_compression': self.video_recording_compress.setChecked,
            'video_recording_resize': self.video_recording_resize.setValue,
            'video_decimation': self.video_decimation.setValue,
            'video_filename': self.video_file.setText,
            'video_codec': self.codec_combobox.setCurrentText,
            'video_gpu': self.use_gpu.setChecked,
            'video_grayscale': self.grayscale.setChecked,
            'video_preset': self.video_preset.setCurrentText,
            'video_quality': self.video_quality.setValue,
            'display_fps': self.display_fps.setValue
        }

        for key, setter in setters.items():
            if key in state:
                setter(state[key])        

if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication, QMainWindow

    class Window(QMainWindow):

        def __init__(self,*args,**kwargs):

            super().__init__(*args, **kwargs)
            self.output_widget = VideoOutputWidget()
            self.setCentralWidget(self.output_widget)
            self.output_widget.state_changed.connect(self.state_changed)

        def state_changed(self):
            print(self.output_widget.get_state())
    
    app = QApplication([])
    window = Window()
    window.show()
    app.exec()
