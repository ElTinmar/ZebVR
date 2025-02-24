from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QPushButton, 
    QLabel,
    QStackedWidget
)
from PyQt5.QtCore import pyqtSignal, Qt
from typing import Dict
from numpy.typing import NDArray
import numpy as np
import cv2
import os

from qt_widgets import (
    LabeledDoubleSpinBox, 
    LabeledSpinBox, 
    LabeledComboBox, 
    NDarray_to_QPixmap, 
    FileSaveLabeledEditButton
)
import numpy as np

class BackgroundWidget(QWidget):

    background_signal = pyqtSignal()
    state_changed = pyqtSignal()
    
    PREVIEW_HEIGHT: int = 512
    DEFAULT_FILE = 'ZebVR/default/background.npy'

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.declare_components()
        self.layout_components()

    def declare_components(self):

        # inpaint background
        self.parameters_inpaint = QWidget()
        
        self.inpaint_radius = LabeledSpinBox()
        self.inpaint_radius.setText('Radius')
        self.inpaint_radius.setRange(0,100)
        self.inpaint_radius.setValue(3)
        self.inpaint_radius.valueChanged.connect(self.state_changed)
        
        self.inpaint_algo = LabeledComboBox(self)
        self.inpaint_algo.setText('algorithm')
        self.inpaint_algo.addItem('navier-stokes')
        self.inpaint_algo.addItem('telea')
        self.inpaint_algo.currentIndexChanged.connect(self.state_changed)

        # static background
        self.parameters_static = QWidget()

        self.static_num_images = LabeledSpinBox()
        self.static_num_images.setText('#images')
        self.static_num_images.setRange(1,10000)
        self.static_num_images.setValue(10)
        self.static_num_images.valueChanged.connect(self.state_changed)

        self.static_pause_duration = LabeledDoubleSpinBox()
        self.static_pause_duration.setText('Time between images (s)')
        self.static_pause_duration.setRange(1,10000)
        self.static_pause_duration.setValue(10)
        self.static_pause_duration.valueChanged.connect(self.state_changed)

        # drop-down list to choose the background subtraction method
        self.bckgsub_method_combobox = LabeledComboBox(self)
        self.bckgsub_method_combobox.setText('method')
        self.bckgsub_method_combobox.addItem('inpaint')
        self.bckgsub_method_combobox.addItem('static')
        self.bckgsub_method_combobox.currentIndexChanged.connect(self.method_change)

        self.bckgsub_polarity_combobox = LabeledComboBox(self)
        self.bckgsub_polarity_combobox.setText('polarity')
        self.bckgsub_polarity_combobox.addItem('dark on bright')
        self.bckgsub_polarity_combobox.addItem('bright on dark')
        self.bckgsub_polarity_combobox.currentIndexChanged.connect(self.state_changed)

        self.bckgsub_parameter_stack = QStackedWidget(self)
        self.bckgsub_parameter_stack.addWidget(self.parameters_inpaint)
        self.bckgsub_parameter_stack.addWidget(self.parameters_static)

        self.background_file = FileSaveLabeledEditButton()
        self.background_file.setLabel('background file:')
        self.background_file.setDefault(self.DEFAULT_FILE)
        self.background_file.textChanged.connect(self.state_changed)

        self.background = QPushButton('background')
        self.background.clicked.connect(self.background_signal)

        self.image = QLabel()
        if os.path.exists(self.DEFAULT_FILE):
            self.set_image(np.load(self.DEFAULT_FILE))
        else:
            self.set_image(np.zeros((512,512), dtype=np.uint8))

    def method_change(self, index: int):
        self.bckgsub_parameter_stack.setCurrentIndex(index)
        self.state_changed.emit()

    def layout_components(self):

        inpaint_layout = QVBoxLayout(self.parameters_inpaint)
        inpaint_layout.addWidget(self.inpaint_radius)
        inpaint_layout.addWidget(self.inpaint_algo)
        inpaint_layout.addStretch()

        static_layout = QVBoxLayout(self.parameters_static)
        static_layout.addWidget(self.static_num_images)
        static_layout.addWidget(self.static_pause_duration)
        static_layout.addStretch()

        image_layout = QHBoxLayout()
        image_layout.addStretch()
        image_layout.addWidget(self.image)
        image_layout.addStretch() 

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.bckgsub_method_combobox)
        main_layout.addWidget(self.bckgsub_parameter_stack)
        main_layout.addWidget(self.bckgsub_polarity_combobox)
        main_layout.addWidget(self.background_file)
        main_layout.addWidget(self.background)
        main_layout.addLayout(image_layout)
    
    def set_image(self, image: NDArray):
        # TODO maybe check that image is uint8
        h, w = image.shape[:2]
        preview_width = int(w * self.PREVIEW_HEIGHT/h)
        image_resized = cv2.resize(image,(preview_width, self.PREVIEW_HEIGHT), cv2.INTER_NEAREST)
        self.image.setPixmap(NDarray_to_QPixmap(image_resized))

    def get_state(self) -> Dict:
        state = {}
        state['inpaint_radius'] = self.inpaint_radius.value()
        state['static_num_images'] = self.static_num_images.value()
        state['static_pause_duration'] = self.static_pause_duration.value()
        state['inpaint_algo'] = self.inpaint_algo.currentText()
        state['bckgsub_method'] = self.bckgsub_method_combobox.currentText()
        state['bckgsub_polarity'] = self.bckgsub_polarity_combobox.currentText()
        state['background_file'] =  self.background_file.text()
        return state
    
    def set_state(self, state: Dict) -> None:
        try:
            self.inpaint_radius.setValue(state['inpaint_radius'])
            self.static_num_images.setValue(state['static_num_images'])
            self.static_pause_duration.setValue(state['static_pause_duration'])
            self.inpaint_algo.setCurrentText(state['inpaint_algo'])
            self.bckgsub_method_combobox.setCurrentText(state['bckgsub_method'])
            self.bckgsub_polarity_combobox.setCurrentText(state['bckgsub_polarity'])
            self.background_file.setText(state['background_file'])

        except KeyError:
            print('Wrong state keys provided to background widget')
            raise

if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication, QMainWindow
    from PyQt5.QtCore import  QRunnable, QThreadPool

    class Window(QMainWindow):

        def __init__(self,*args,**kwargs):

            super().__init__(*args, **kwargs)
            self.background_widget = BackgroundWidget()
            self.setCentralWidget(self.background_widget)
            self.background_widget.background_signal.connect(self.background)
            self.background_widget.state_changed.connect(self.state_changed)

        def background(self):
            print('background clicked')

        def state_changed(self):
            print(self.background_widget.get_state())
    
    app = QApplication([])
    window = Window()
    window.show()
    app.exec()
