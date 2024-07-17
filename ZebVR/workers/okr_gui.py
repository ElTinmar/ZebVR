from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from qt_widgets import LabeledDoubleSpinBox
from ZebVR.config import OKR_SPATIAL_FREQUENCY_DEG, OKR_GRATING_SPEED_DEG_PER_SEC

class OKR_GUI(WorkerNode):
    
    def initialize(self) -> None:
        super().initialize()
        self.updated = False
        self.app = QApplication([])
        self.window = QWidget()
        self.declare_components()
        self.layout_components()
        self.window.setWindowTitle('OKR controls')
        self.window.show()

    def declare_components(self):
        # spatial freq (degrees)
        self.spatial_freq = LabeledDoubleSpinBox()
        self.spatial_freq.setText('Spatial frequence (deg)')
        self.spatial_freq.setRange(0,10_000)
        self.spatial_freq.setValue(OKR_SPATIAL_FREQUENCY_DEG)
        self.spatial_freq.valueChanged.connect(self.on_change)

        self.speed = LabeledDoubleSpinBox()
        self.speed.setText('speed (deg/s)')
        self.speed.setRange(-10_000,10_000)
        self.speed.setValue(OKR_GRATING_SPEED_DEG_PER_SEC)
        self.speed.valueChanged.connect(self.on_change)

    def layout_components(self):
        layout = QVBoxLayout(self.window)
        layout.addWidget(self.spatial_freq)
        layout.addWidget(self.speed)

    def on_change(self):
        self.updated = True

    def process_data(self, data: None) -> NDArray:
        self.app.processEvents()

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        # send only one message when things are changed
        if self.updated:
            res = {}
            res['visual_stim_control'] = {}
            res['visual_stim_control']['okr_grating_speed_deg_per_sec'] = self.speed.value() 
            res['visual_stim_control']['okr_spatial_frequency_deg'] = self.spatial_freq.value()
            self.updated = False
            return res       
        else:
            return None