from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QPushButton, 
    QLabel
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
from typing import Dict, List
from pathlib import Path
import json

from qt_widgets import LabeledDoubleSpinBox, LabeledSpinBox, FileSaveLabeledEditButton

# TODO 
# add widget for CALIBRATION_CHECK_DIAMETER_MM
# add widget to change the reticle center

class CalibrationWidget(QWidget):

    calibration_signal = pyqtSignal()
    check_calibration_signal = pyqtSignal()
    state_changed = pyqtSignal()

    CHECKERBOARD_TOOLTIP: str = "Printed checkerboard target size (internal corners)"
    CALIBRATION_CHECK_DIAMETER_MM: List[float]  = [15, 30, 45, 60] 
    DEFAULT_FILE: Path = Path('ZebVR/default/calibration.json')
    PIXMAP_HEIGHT: int = 192

    def __init__(self, *args, **kwargs)  -> None:

        super().__init__(*args, **kwargs)
        
        self.declare_components()
        self.layout_components()

    def declare_components(self) -> None:

        self.explanation = QLabel('To calibrate, place the calibration target under the camera. Ensure proper illumination with the IR light.')
        self.checkerboard = QLabel()
        self.checkerboard.setPixmap(QPixmap('ZebVR/resources/checkerboard.png').scaledToHeight(self.PIXMAP_HEIGHT,Qt.SmoothTransformation))

        self.explanation_check = QLabel('To check calibration, place the reticle under the camera')
        self.reticle = QLabel()
        self.reticle.setPixmap(QPixmap('ZebVR/resources/reticle.png').scaledToHeight(self.PIXMAP_HEIGHT,Qt.SmoothTransformation))
        
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
        self.checkerboard_grid_size_x.setToolTip(self.CHECKERBOARD_TOOLTIP)

        self.checkerboard_grid_size_y = LabeledSpinBox()
        self.checkerboard_grid_size_y.setText('# inner corner Y:')
        self.checkerboard_grid_size_y.setRange(0, 20)
        self.checkerboard_grid_size_y.setValue(6)
        self.checkerboard_grid_size_y.valueChanged.connect(self.state_changed)
        self.checkerboard_grid_size_y.setToolTip(self.CHECKERBOARD_TOOLTIP)

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
        self.reticle_thickness.setRange(1, 20)
        self.reticle_thickness.setValue(10.0)
        self.reticle_thickness.valueChanged.connect(self.state_changed)

        self.reticle_center_x = LabeledDoubleSpinBox()
        self.reticle_center_x.setText('reticle X (px):')
        self.reticle_center_x.setRange(0, 100_000)
        self.reticle_center_x.setValue(0.0)
        self.reticle_center_x.valueChanged.connect(self.state_changed)

        self.reticle_center_y = LabeledDoubleSpinBox()
        self.reticle_center_y.setText('reticle Y (px):')
        self.reticle_center_y.setRange(0, 100_000)
        self.reticle_center_y.setValue(0.0)
        self.reticle_center_y.valueChanged.connect(self.state_changed)

        self.calibration_file = FileSaveLabeledEditButton()
        self.calibration_file.setLabel('calibration file:')
        self.calibration_file.setDefault(str(self.DEFAULT_FILE))
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

        if self.DEFAULT_FILE.exists():
            with open(self.DEFAULT_FILE, 'r') as f:
                pix_per_mm = json.load(f)
            self.pix_per_mm.setValue(pix_per_mm)

    def layout_components(self) -> None:

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.calibration)
        button_layout.addWidget(self.check_calibration)

        layout_grid_size = QHBoxLayout()
        layout_grid_size.addWidget(self.checkerboard_grid_size_x)
        layout_grid_size.addWidget(self.checkerboard_grid_size_y)
        layout_grid_size.setSpacing(50)

        layout_checkerboard = QHBoxLayout()
        layout_checkerboard.addStretch()
        layout_checkerboard.addWidget(self.checkerboard)
        layout_checkerboard.addStretch()

        layout_reticle = QHBoxLayout()
        layout_reticle.addStretch()
        layout_reticle.addWidget(self.reticle)
        layout_reticle.addStretch()

        layout_reticle_center = QHBoxLayout()
        layout_reticle_center.addWidget(self.reticle_center_x)
        layout_reticle_center.addWidget(self.reticle_center_y)
        layout_reticle_center.setSpacing(50)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.explanation)
        main_layout.addSpacing(10)
        main_layout.addLayout(layout_checkerboard)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.explanation_check)
        main_layout.addSpacing(10)
        main_layout.addLayout(layout_reticle)
        main_layout.addSpacing(20)
        main_layout.addWidget(self.checkerboard_square_size_mm)
        main_layout.addLayout(layout_grid_size)
        main_layout.addWidget(self.camera_exposure_ms)
        main_layout.addWidget(self.camera_fps)
        main_layout.addWidget(self.reticle_thickness)
        main_layout.addLayout(layout_reticle_center)
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
        state['reticle_center'] = (self.reticle_center_x.value(), self.reticle_center_y.value())
        state['calibration_file'] = self.calibration_file.text()
        return state
    
    def set_state(self, state: Dict) -> None:

        setters = {
            'checkerboard_square_size_mm': self.checkerboard_square_size_mm.setValue,
            'checkerboard_grid_size': lambda x: (
                self.checkerboard_grid_size_x.setValue(x[0]),
                self.checkerboard_grid_size_y.setValue(x[1]),
            ),
            'camera_exposure_ms': self.camera_exposure_ms.setValue,
            'camera_fps': self.camera_fps.setValue,
            'pix_per_mm': self.pix_per_mm.setValue,
            'calibration_file': self.calibration_file.setText,
            'reticle_thickness': self.reticle_thickness.setValue,
            'reticle_center': lambda x: (
                self.reticle_center_x.setValue(x[0]),
                self.reticle_center_y.setValue(x[1])
            )
        }

        for key, setter in setters.items():
            if key in state:
                try:
                    setter(state[key])
                except Exception as e:
                    print(e)

if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication, QMainWindow

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
