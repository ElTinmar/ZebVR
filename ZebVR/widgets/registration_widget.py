from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QPushButton, 
    QFrame, 
    QHeaderView, 
    QTableWidget, 
    QTableWidgetItem
)
from PyQt5.QtCore import pyqtSignal, Qt
from typing import Dict

from qt_widgets import LabeledDoubleSpinBox, LabeledSpinBox

class RegistrationWidget(QWidget):

    state_changed = pyqtSignal()

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.declare_components()
        self.layout_components()
    
    def declare_components(self):
        
        self.detection_threshold = LabeledDoubleSpinBox()
        self.detection_threshold.setText('intensity threshold:')
        self.detection_threshold.setRange(0, 1)
        self.detection_threshold.setValue(0.15)

        self.image_contrast = LabeledDoubleSpinBox()
        self.image_contrast.setText('contrast:')
        self.image_contrast.setRange(0, 10)
        self.image_contrast.setValue(1.0)

        self.image_gamma = LabeledDoubleSpinBox()
        self.image_gamma.setText('gamma:')
        self.image_gamma.setRange(0, 10)
        self.image_gamma.setValue(1.0)

        self.image_brightness = LabeledDoubleSpinBox()
        self.image_brightness.setText('brightness:')
        self.image_brightness.setRange(0, 10)
        self.image_brightness.setValue(1.0)

        self.dot_radius_px = LabeledDoubleSpinBox()
        self.dot_radius_px.setText('dot radius (px):')
        self.dot_radius_px.setRange(0, 1_000)
        self.dot_radius_px.setValue(10.0)

        self.dot_steps = LabeledSpinBox()
        self.dot_steps.setText('#dot step:')
        self.dot_steps.setRange(0, 1_000)
        self.dot_steps.setValue(11)

        self.dot_fps = LabeledDoubleSpinBox()
        self.dot_fps.setText('FPS dot:')
        self.dot_fps.setRange(0, 1_000)
        self.dot_fps.setValue(5)

        self.bar_width_px = LabeledDoubleSpinBox()
        self.bar_width_px.setText('bar width (px):')
        self.bar_width_px.setRange(0, 1_000)
        self.bar_width_px.setValue(10.0)

        self.bar_step_px = LabeledSpinBox()
        self.bar_step_px.setText('bar step size (px):')
        self.bar_step_px.setRange(0, 1_000)
        self.bar_step_px.setValue(200)

        self.bar_fps = LabeledDoubleSpinBox()
        self.bar_fps.setText('FPS bar:')
        self.bar_fps.setRange(0, 1_000)
        self.bar_fps.setValue(30)

        self.camera_exposure_ms = LabeledDoubleSpinBox()
        self.camera_exposure_ms.setText('camera exposure (ms):')
        self.camera_exposure_ms.setRange(0, 100_000)
        self.camera_exposure_ms.setValue(5_000)

        self.pattern_intensity = LabeledSpinBox()
        self.pattern_intensity.setText('pattern intensity')
        self.pattern_intensity.setRange(1, 255)
        self.pattern_intensity.setValue(64)

        self.registration = QPushButton('registration')

        self.check_registration = QPushButton('check')
        
        self.transformation_matrix_table = QTableWidget()
        self.transformation_matrix_table.setRowCount(3)
        self.transformation_matrix_table.setColumnCount(3)  
        self.transformation_matrix_table.setItem(0,0,QTableWidgetItem('1.0'))
        self.transformation_matrix_table.setItem(0,1,QTableWidgetItem('0.0'))
        self.transformation_matrix_table.setItem(0,2,QTableWidgetItem('0.0'))
        self.transformation_matrix_table.setItem(1,0,QTableWidgetItem('0.0'))
        self.transformation_matrix_table.setItem(1,1,QTableWidgetItem('1.0'))
        self.transformation_matrix_table.setItem(1,2,QTableWidgetItem('0.0'))
        self.transformation_matrix_table.setItem(2,0,QTableWidgetItem('0.0'))
        self.transformation_matrix_table.setItem(2,1,QTableWidgetItem('0.0'))
        self.transformation_matrix_table.setItem(2,2,QTableWidgetItem('1.0'))
        self.transformation_matrix_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.transformation_matrix_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.transformation_matrix_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.transformation_matrix_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.transformation_matrix_table.horizontalHeader().hide()
        self.transformation_matrix_table.verticalHeader().hide()
        self.transformation_matrix_table.setFrameShape(QFrame.NoFrame)
        self.transformation_matrix_table.setMaximumHeight(100)
        self.transformation_matrix_table.setEnabled(False)

    def layout_components(self):

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.registration)
        button_layout.addWidget(self.check_registration)

        main_layout = QVBoxLayout(self)
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
        return state
    
    def set_state(self, state: Dict) -> None:
        pass

if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication, QMainWindow
    from PyQt5.QtCore import  QRunnable, QThreadPool

    class Window(QMainWindow):

        def __init__(self,*args,**kwargs):

            super().__init__(*args, **kwargs)
            self.registration_widget = RegistrationWidget()
            self.setCentralWidget(self.registration_widget)
    
    app = QApplication([])
    window = Window()
    window.show()
    app.exec()
