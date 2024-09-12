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
from PyQt5.QtGui import QPixmap
from typing import Dict

from qt_widgets import LabeledDoubleSpinBox, LabeledSpinBox, FileSaveLabeledEditButton

class CalibrationWidget(QWidget):

    calibration_signal = pyqtSignal()
    check_calibration_signal = pyqtSignal()
    state_changed = pyqtSignal()
    checkerboard_tooltip = "Printed checkerboard target size (internal corners)"
    CALIBRATION_CHECK_DIAMETER_MM  = [15, 30, 45, 60] #TODO make a list out of that

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        
        self.declare_components()
        self.layout_components()

    def declare_components(self):

        self.explanation = QLabel('To calibrate, place the calibration target under the camera')
        self.checkerboard = QLabel()
        self.checkerboard.setPixmap(QPixmap('ZebVR/resources/checkerboard.png'))

        self.explanation_check = QLabel('To check calibration, place the reticle under the camera')
        self.reticle = QLabel()
        self.reticle.setPixmap(QPixmap('ZebVR/resources/reticle.png'))
        
        self.checkerboard_square_size_mm = LabeledDoubleSpinBox()
        self.checkerboard_square_size_mm.setText('checkerboard square size (mm):')
        self.checkerboard_square_size_mm.setRange(0, 100)
        self.checkerboard_square_size_mm.setSingleStep(0.5)
        self.checkerboard_square_size_mm.setValue(2)
        self.checkerboard_square_size_mm.valueChanged.connect(self.state_changed)

        self.checkerboard_grid_size_x = LabeledSpinBox()
        self.checkerboard_grid_size_x.setText('# inner corner X:')
        self.checkerboard_grid_size_x.setRange(0, 20)
        self.checkerboard_grid_size_x.setValue(9)
        self.checkerboard_grid_size_x.valueChanged.connect(self.state_changed)
        self.checkerboard_grid_size_x.setToolTip(self.checkerboard_tooltip)

        self.checkerboard_grid_size_y = LabeledSpinBox()
        self.checkerboard_grid_size_y.setText('# inner corner Y:')
        self.checkerboard_grid_size_y.setRange(0, 20)
        self.checkerboard_grid_size_y.setValue(6)
        self.checkerboard_grid_size_y.valueChanged.connect(self.state_changed)
        self.checkerboard_grid_size_y.setToolTip(self.checkerboard_tooltip)

        self.camera_fps = LabeledDoubleSpinBox()
        self.camera_fps.setText('camera FPS:')
        self.camera_fps.setRange(0, 1_000)
        self.camera_fps.setValue(10)
        self.camera_fps.valueChanged.connect(self.state_changed)

        self.camera_exposure_ms = LabeledDoubleSpinBox()
        self.camera_exposure_ms.setText('camera exposure (ms):')
        self.camera_exposure_ms.setRange(0, 100_000)
        self.camera_exposure_ms.setValue(5_000)
        self.camera_exposure_ms.valueChanged.connect(self.state_changed)

        self.reticle_thickness = LabeledDoubleSpinBox()
        self.reticle_thickness.setText('reticle thickness (px):')
        self.reticle_thickness.setRange(0, 20)
        self.reticle_thickness.setValue(10.0)
        self.reticle_thickness.valueChanged.connect(self.state_changed)

        self.calibration_file = FileSaveLabeledEditButton()
        self.calibration_file.setLabel('calibration file:')
        self.calibration_file.setDefault('ZebVR/default/calibration.json')
        self.calibration_file.textChanged.connect(self.state_changed)

        self.calibration = QPushButton('calibration')
        self.calibration.clicked.connect(self.calibration_signal)

        self.check_calibration = QPushButton('check')
        self.check_calibration.clicked.connect(self.check_calibration_signal)

        self.pix_per_mm = LabeledDoubleSpinBox()
        self.pix_per_mm.setText('pix/mm:')
        self.pix_per_mm.setRange(0, 10_000)
        self.pix_per_mm.setValue(0)
        self.pix_per_mm.valueChanged.connect(self.state_changed)

    def layout_components(self):

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.calibration)
        button_layout.addWidget(self.check_calibration)

        layout_grid_size = QHBoxLayout()
        layout_grid_size.addWidget(self.checkerboard_grid_size_x)
        layout_grid_size.addWidget(self.checkerboard_grid_size_y)

        layout_checkerboard = QHBoxLayout()
        layout_checkerboard.addStretch()
        layout_checkerboard.addWidget(self.checkerboard)
        layout_checkerboard.addStretch()

        layout_reticle = QHBoxLayout()
        layout_reticle.addStretch()
        layout_reticle.addWidget(self.reticle)
        layout_reticle.addStretch()

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.explanation)
        main_layout.addLayout(layout_checkerboard)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.explanation_check)
        main_layout.addLayout(layout_reticle)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.checkerboard_square_size_mm)
        main_layout.addLayout(layout_grid_size)
        main_layout.addWidget(self.camera_exposure_ms)
        main_layout.addWidget(self.camera_fps)
        main_layout.addWidget(self.reticle_thickness)
        main_layout.addWidget(self.calibration_file)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.pix_per_mm)
        main_layout.addStretch()

    def get_state(self) -> Dict:
        state = {}
        state['checkerboard_square_size_mm'] = self.checkerboard_square_size_mm.value()
        state['checkerboard_grid_size'] = (self.checkerboard_grid_size_x.value(), self.checkerboard_grid_size_y.value())
        state['camera_exposure_ms'] = self.camera_exposure_ms.value()
        state['camera_fps'] = self.camera_fps.value()
        state['pix_per_mm'] = self.pix_per_mm.value()
        state['reticle_thickness'] = self.reticle_thickness.value()
        state['calibration_file'] = self.calibration_file.text()
        return state
    
    def set_state(self, state: Dict) -> None:
        try:
            self.checkerboard_square_size_mm.setValue(state['checkerboard_square_size_mm'])
            self.checkerboard_grid_size_x.setValue(state['checkerboard_grid_size'][0])
            self.checkerboard_grid_size_y.setValue(state['checkerboard_grid_size'][1])
            self.camera_exposure_ms.setValue(state['camera_exposure_ms'])
            self.camera_fps.setValue(state['camera_fps'])
            self.pix_per_mm.setValue(state['pix_per_mm'])
            self.calibration_file.setText(state['calibration_file'])
            self.reticle_thickness.setValue(state['reticle_thickness'])

        except KeyError:
            print('Wrong state keys provided to calibration widget')
            raise

if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication, QMainWindow
    from PyQt5.QtCore import  QRunnable, QThreadPool

    class Window(QMainWindow):

        def __init__(self,*args,**kwargs):

            super().__init__(*args, **kwargs)
            self.calibration_widget = CalibrationWidget()
            self.setCentralWidget(self.calibration_widget)
            self.calibration_widget.calibration_signal.connect(self.calibration)
            self.calibration_widget.check_calibration_signal.connect(self.check_calibration)
            self.calibration_widget.state_changed.connect(self.state_changed)

        def calibration(self):
            print('calibration clicked')

        def check_calibration(self):
            print('check calibration clicked')

        def state_changed(self):
            print(self.calibration_widget.get_state())
    
    app = QApplication([])
    window = Window()
    window.show()
    app.exec()
