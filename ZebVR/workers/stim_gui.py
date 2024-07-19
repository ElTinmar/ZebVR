from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional
from qt_widgets import LabeledDoubleSpinBox

from PyQt5.QtWidgets import (
    QApplication, 
    QWidget, 
    QCheckBox, 
    QStackedWidget, 
    QGroupBox, 
    QVBoxLayout, 
    QComboBox
)

from ZebVR.config import (
    PHOTOTAXIS_POLARITY, 
    OMR_SPATIAL_FREQUENCY_DEG, 
    OMR_SPEED_DEG_PER_SEC, 
    OMR_ANGLE_DEG,
    OKR_SPATIAL_FREQUENCY_DEG, 
    OKR_SPEED_DEG_PER_SEC,
    LOOMING_CENTER_MM,
    LOOMING_EXPANSION_SPEED_MM_PER_SEC,
    LOOMING_EXPANSION_TIME_SEC,
    LOOMING_PERIOD_SEC
)

class StimGUI(WorkerNode):

    def initialize(self) -> None:
        super().initialize()
        self.updated = False
        self.app = QApplication([])
        self.window = QWidget()
        self.declare_components()
        self.layout_components()
        self.window.setWindowTitle('Visual stim controls')
        self.window.show()

    def declare_components(self):

        self.stim_select = QComboBox()
        self.stim_select.addItem('Phototaxis')
        self.stim_select.addItem('OMR')
        self.stim_select.addItem('OKR')
        self.stim_select.addItem('Looming')
        self.stim_select.currentIndexChanged.connect(self.stim_changed)

        # Phototaxis
        self.phototaxis_polarity = QCheckBox('invert polarity', self.window)
        self.phototaxis_polarity.stateChanged.connect(self.on_change)
        self.phototaxis_polarity.setChecked(PHOTOTAXIS_POLARITY)

        # OMR
        self.omr_spatial_freq = LabeledDoubleSpinBox()
        self.omr_spatial_freq.setText('Spatial frequency (deg)')
        self.omr_spatial_freq.setRange(0,10_000)
        self.omr_spatial_freq.setValue(OMR_SPATIAL_FREQUENCY_DEG)
        self.omr_spatial_freq.valueChanged.connect(self.on_change)

        self.omr_angle = LabeledDoubleSpinBox()
        self.omr_angle.setText('Grating angle (deg)')
        self.omr_angle.setRange(0,360)
        self.omr_angle.setValue(OMR_ANGLE_DEG)
        self.omr_angle.valueChanged.connect(self.on_change)

        self.omr_speed = LabeledDoubleSpinBox()
        self.omr_speed.setText('Grating speed (deg/s)')
        self.omr_speed.setRange(-10_000,10_000)
        self.omr_speed.setValue(OMR_SPEED_DEG_PER_SEC)
        self.omr_speed.valueChanged.connect(self.on_change)

        # OKR
        self.okr_spatial_freq = LabeledDoubleSpinBox()
        self.okr_spatial_freq.setText('Spatial frequence (deg)')
        self.okr_spatial_freq.setRange(0,10_000)
        self.okr_spatial_freq.setValue(OKR_SPATIAL_FREQUENCY_DEG)
        self.okr_spatial_freq.valueChanged.connect(self.on_change)

        self.okr_speed = LabeledDoubleSpinBox()
        self.okr_speed.setText('speed (deg/s)')
        self.okr_speed.setRange(-10_000,10_000)
        self.okr_speed.setValue(OKR_SPEED_DEG_PER_SEC)
        self.okr_speed.valueChanged.connect(self.on_change)

        # Looming
        self.looming_center_mm_x = LabeledDoubleSpinBox()
        self.looming_center_mm_x.setText('X (mm)')
        self.looming_center_mm_x.setRange(-10_000,10_000)
        self.looming_center_mm_x.setValue(LOOMING_CENTER_MM[0])
        self.looming_center_mm_x.valueChanged.connect(self.on_change)

        self.looming_center_mm_y = LabeledDoubleSpinBox()
        self.looming_center_mm_y.setText('Y (mm)')
        self.looming_center_mm_y.setRange(-10_000,10_000)
        self.looming_center_mm_y.setValue(LOOMING_CENTER_MM[1])
        self.looming_center_mm_y.valueChanged.connect(self.on_change)

        self.looming_period_sec = LabeledDoubleSpinBox()
        self.looming_period_sec.setText('period (s)')
        self.looming_period_sec.setRange(0,100_000)
        self.looming_period_sec.setValue(LOOMING_PERIOD_SEC)
        self.looming_period_sec.valueChanged.connect(self.on_change)

        self.looming_expansion_time_sec = LabeledDoubleSpinBox()
        self.looming_expansion_time_sec.setText('expansion time (s)')
        self.looming_expansion_time_sec.setRange(0,100_000)
        self.looming_expansion_time_sec.setValue(LOOMING_EXPANSION_TIME_SEC)
        self.looming_expansion_time_sec.valueChanged.connect(self.on_change)

        self.looming_expansion_speed_mm_per_sec = LabeledDoubleSpinBox()
        self.looming_expansion_speed_mm_per_sec.setText('expansion speed (mm/s)')
        self.looming_expansion_speed_mm_per_sec.setRange(0,100_000)
        self.looming_expansion_speed_mm_per_sec.setValue(LOOMING_EXPANSION_SPEED_MM_PER_SEC)
        self.looming_expansion_speed_mm_per_sec.valueChanged.connect(self.on_change)

    def layout_components(self):

        phototaxis_layout = QVBoxLayout()
        phototaxis_layout.addWidget(self.phototaxis_polarity)
        self.phototaxis_group = QGroupBox('Phototaxis parameters')
        self.phototaxis_group.setLayout(phototaxis_layout)

        omr_layout = QVBoxLayout()
        omr_layout.addWidget(self.omr_spatial_freq)
        omr_layout.addWidget(self.omr_angle)
        omr_layout.addWidget(self.omr_speed)
        self.omr_group = QGroupBox('OMR parameters')
        self.omr_group.setLayout(omr_layout)

        okr_layout = QVBoxLayout()
        okr_layout.addWidget(self.okr_spatial_freq)
        okr_layout.addWidget(self.okr_speed)
        self.okr_group = QGroupBox('OKR parameters')
        self.okr_group.setLayout(okr_layout)

        looming_layout = QVBoxLayout()
        looming_layout.addWidget(self.looming_center_mm_x)
        looming_layout.addWidget(self.looming_center_mm_y)
        looming_layout.addWidget(self.looming_period_sec)
        looming_layout.addWidget(self.looming_expansion_time_sec)
        looming_layout.addWidget(self.looming_expansion_speed_mm_per_sec)
        self.looming_group = QGroupBox('Looming parameters')
        self.looming_group.setLayout(looming_layout)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.phototaxis_group)
        self.stack.addWidget(self.omr_group)
        self.stack.addWidget(self.okr_group)
        self.stack.addWidget(self.looming_group)
    
        layout = QVBoxLayout(self.window)
        layout.addWidget(self.stim_select)
        layout.addWidget(self.stack)

    def stim_changed(self):
        self.stack.setCurrentIndex(self.stim_select.currentIndex())
        self.on_change()

    def on_change(self):
        self.updated = True

    def process_data(self, data: None) -> NDArray:
        self.app.processEvents()

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        # send only one message when things are changed
        if self.updated:
            res = {}
            res['visual_stim_control'] = {}
            res['visual_stim_control']['stim_select'] = self.stim_select.currentIndex()
            res['visual_stim_control']['phototaxis_polarity'] = -1+2*self.phototaxis_polarity.isChecked()
            res['visual_stim_control']['omr_spatial_frequency_deg'] = self.omr_spatial_freq.value() 
            res['visual_stim_control']['omr_angle_deg'] = self.omr_angle.value()
            res['visual_stim_control']['omr_speed_deg_per_sec'] = self.omr_speed.value() 
            res['visual_stim_control']['okr_spatial_frequency_deg'] = self.okr_spatial_freq.value()
            res['visual_stim_control']['okr_speed_deg_per_sec'] = self.okr_speed.value()
            res['visual_stim_control']['looming_center_mm_x'] = self.looming_center_mm_x.value()
            res['visual_stim_control']['looming_center_mm_y'] = self.looming_center_mm_y.value()
            res['visual_stim_control']['looming_period_sec'] = self.looming_period_sec.value()
            res['visual_stim_control']['looming_expansion_time_sec'] = self.looming_expansion_time_sec.value()
            res['visual_stim_control']['looming_expansion_speed_mm_per_sec'] = self.looming_expansion_speed_mm_per_sec.value()

            self.updated = False
            return res       
        else:
            return None
        