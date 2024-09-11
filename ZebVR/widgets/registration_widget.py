from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QPushButton, 
    QFrame, 
    QHeaderView, 
    QTableWidget, 
    QTableWidgetItem,
    QLabel
)
from PyQt5.QtCore import pyqtSignal, Qt
from typing import Dict

from qt_widgets import LabeledDoubleSpinBox, LabeledSpinBox

class RegistrationWidget(QWidget):

    registration_signal = pyqtSignal()
    check_registration_signal = pyqtSignal()
    state_changed = pyqtSignal()

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        
        self.transformation_matrix = [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0]
        ]

        self.declare_components()
        self.layout_components()

    
    def declare_components(self):

        self.explanation = QLabel(
            "The projector light must be visible on camera. \n"
            "Please ensure that the IR longpass filter has been removed, \n"
            "and that the IR light is off."
        )
        
        self.detection_threshold = LabeledDoubleSpinBox()
        self.detection_threshold.setText('intensity threshold:')
        self.detection_threshold.setRange(0, 1)
        self.detection_threshold.setSingleStep(0.01)
        self.detection_threshold.setValue(0.15)
        self.detection_threshold.valueChanged.connect(self.state_changed)

        self.image_contrast = LabeledDoubleSpinBox()
        self.image_contrast.setText('contrast:')
        self.image_contrast.setRange(0, 10)
        self.image_contrast.setSingleStep(0.05)
        self.image_contrast.setValue(1.0)
        self.image_contrast.valueChanged.connect(self.state_changed)

        self.image_gamma = LabeledDoubleSpinBox()
        self.image_gamma.setText('gamma:')
        self.image_gamma.setRange(0, 10)
        self.image_gamma.setSingleStep(0.05)
        self.image_gamma.setValue(1.0)
        self.image_gamma.valueChanged.connect(self.state_changed)

        self.image_brightness = LabeledDoubleSpinBox()
        self.image_brightness.setText('brightness:')
        self.image_brightness.setRange(0, 10)
        self.image_brightness.setSingleStep(0.05)
        self.image_brightness.setValue(1.0)
        self.image_brightness.valueChanged.connect(self.state_changed)

        self.dot_radius_px = LabeledDoubleSpinBox()
        self.dot_radius_px.setText('dot radius (px):')
        self.dot_radius_px.setRange(0, 1_000)
        self.dot_radius_px.setSingleStep(0.5)
        self.dot_radius_px.setValue(10.0)
        self.dot_radius_px.valueChanged.connect(self.state_changed)

        self.dot_steps = LabeledSpinBox()
        self.dot_steps.setText('#dot step:')
        self.dot_steps.setRange(0, 1_000)
        self.dot_steps.setValue(11)
        self.dot_steps.valueChanged.connect(self.state_changed)

        self.dot_fps = LabeledDoubleSpinBox()
        self.dot_fps.setText('FPS dot:')
        self.dot_fps.setRange(0, 1_000)
        self.dot_fps.setValue(5)
        self.dot_fps.valueChanged.connect(self.state_changed)

        self.bar_width_px = LabeledDoubleSpinBox()
        self.bar_width_px.setText('bar width (px):')
        self.bar_width_px.setRange(0, 1_000)
        self.bar_width_px.setValue(10.0)
        self.bar_width_px.valueChanged.connect(self.state_changed)

        self.bar_step_px = LabeledSpinBox()
        self.bar_step_px.setText('bar step size (px):')
        self.bar_step_px.setRange(0, 1_000)
        self.bar_step_px.setValue(200)
        self.bar_step_px.valueChanged.connect(self.state_changed)

        self.bar_fps = LabeledDoubleSpinBox()
        self.bar_fps.setText('FPS bar:')
        self.bar_fps.setRange(0, 1_000)
        self.bar_fps.setValue(30)
        self.bar_fps.valueChanged.connect(self.state_changed)

        self.camera_exposure_ms = LabeledDoubleSpinBox()
        self.camera_exposure_ms.setText('camera exposure (ms):')
        self.camera_exposure_ms.setRange(0, 100_000)
        self.camera_exposure_ms.setValue(5_000)
        self.camera_exposure_ms.valueChanged.connect(self.state_changed)

        self.pattern_intensity = LabeledSpinBox()
        self.pattern_intensity.setText('pattern intensity')
        self.pattern_intensity.setRange(1, 255)
        self.pattern_intensity.setValue(64)
        self.pattern_intensity.valueChanged.connect(self.state_changed)

        self.registration = QPushButton('registration')
        self.registration.clicked.connect(self.registration_signal)

        self.check_registration = QPushButton('check')
        self.check_registration.clicked.connect(self.check_registration_signal)
        
        self.transformation_matrix_table = QTableWidget()
        self.transformation_matrix_table.setRowCount(3)
        self.transformation_matrix_table.setColumnCount(3)  
        self.transformation_matrix_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.transformation_matrix_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.transformation_matrix_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.transformation_matrix_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.transformation_matrix_table.horizontalHeader().hide()
        self.transformation_matrix_table.verticalHeader().hide()
        self.transformation_matrix_table.setFrameShape(QFrame.NoFrame)
        self.transformation_matrix_table.setMaximumHeight(100)
        self.transformation_matrix_table.setEnabled(False)
        self.update_table()

    def update_table(self):
        for i in range(3):
            for j in range(3):
                self.transformation_matrix_table.setItem(i,j,QTableWidgetItem(f'{self.transformation_matrix[i][j]:2f}'))

    def layout_components(self):

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.registration)
        button_layout.addWidget(self.check_registration)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.explanation)
        main_layout.addWidget(QLabel('')) # Just for spacing
        main_layout.addWidget(self.detection_threshold)
        main_layout.addWidget(self.image_contrast)
        main_layout.addWidget(self.image_gamma)
        main_layout.addWidget(self.image_brightness)
        main_layout.addWidget(self.dot_radius_px)
        main_layout.addWidget(self.dot_steps)
        main_layout.addWidget(self.dot_fps)
        main_layout.addWidget(self.bar_width_px)
        main_layout.addWidget(self.bar_step_px)
        main_layout.addWidget(self.bar_fps)
        main_layout.addWidget(self.camera_exposure_ms)
        main_layout.addWidget(self.pattern_intensity)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.transformation_matrix_table)
        main_layout.addStretch()

    def get_state(self) -> Dict:
        state = {}
        state['detection_threshold'] = self.detection_threshold.value()
        state['image_contrast'] = self.image_contrast.value()
        state['image_gamma'] = self.image_gamma.value()
        state['image_brightness'] = self.image_brightness.value()
        state['dot_radius_px'] = self.dot_radius_px.value()
        state['dot_steps'] = self.dot_steps.value()
        state['dot_fps'] = self.dot_fps.value()
        state['bar_width_px'] = self.bar_width_px.value()
        state['bar_step_px'] = self.bar_step_px.value()
        state['bar_fps'] = self.bar_fps.value()
        state['camera_exposure_ms'] = self.camera_exposure_ms.value()
        state['pattern_intensity'] = self.pattern_intensity.value()
        state['transformation_matrix'] = self.transformation_matrix
        return state
    
    def set_state(self, state: Dict) -> None:
        try:
            self.detection_threshold.setValue(state['detection_threshold'])
            self.image_contrast.setValue(state['image_contrast'])
            self.image_gamma.setValue(state['image_gamma'])
            self.image_brightness.setValue(state['image_brightness'])
            self.dot_radius_px.setValue(state['dot_radius_px'])
            self.dot_steps.setValue(state['dot_steps'])
            self.dot_fps.setValue(state['dot_fps'])
            self.bar_width_px.setValue(state['bar_width_px'])
            self.bar_step_px.setValue(state['bar_step_px'])
            self.bar_fps.setValue(state['bar_fps'])
            self.camera_exposure_ms.setValue(state['camera_exposure_ms'])
            self.pattern_intensity.setValue(state['pattern_intensity'])
            self.transformation_matrix = state['transformation_matrix']
            self.update_table()

        except KeyError:
            print('Wrong state keys provided to registration widget')
            raise

if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication, QMainWindow
    from PyQt5.QtCore import  QRunnable, QThreadPool

    class Window(QMainWindow):

        def __init__(self,*args,**kwargs):

            super().__init__(*args, **kwargs)
            self.registration_widget = RegistrationWidget()
            self.setCentralWidget(self.registration_widget)
            self.registration_widget.registration_signal.connect(self.registration)
            self.registration_widget.check_registration_signal.connect(self.check_registration)
            self.registration_widget.state_changed.connect(self.state_changed)

        def registration(self):
            print('registration clicked')

        def check_registration(self):
            print('check registration clicked')

        def state_changed(self):
            print(self.registration_widget.get_state())
    
    app = QApplication([])
    window = Window()
    window.show()
    app.exec()
