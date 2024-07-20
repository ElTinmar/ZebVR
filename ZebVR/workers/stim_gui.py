from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional, Tuple
from qt_widgets import LabeledDoubleSpinBox

from PyQt5.QtWidgets import (
    QApplication, 
    QWidget, 
    QCheckBox, 
    QStackedWidget, 
    QGroupBox, 
    QVBoxLayout, 
    QComboBox,
    QLabel
)

class StimGUI(WorkerNode):

    def __init__(
            self, 
            phototaxis_polarity: int = 1,
            omr_spatial_frequency_deg: float = 20,
            omr_angle_deg: float = 0,
            omr_speed_deg_per_sec: float = 360,
            okr_spatial_frequency_deg: float = 45,
            okr_speed_deg_per_sec: float = 60,
            looming_center_mm: Tuple = (1,1),
            looming_period_sec: float = 30,
            looming_expansion_time_sec: float = 3,
            looming_expansion_speed_mm_per_sec: float = 10,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)

        self.phototaxis_polarity = phototaxis_polarity
        self.omr_spatial_frequency_deg = omr_spatial_frequency_deg
        self.omr_angle_deg = omr_angle_deg
        self.omr_speed_deg_per_sec = omr_speed_deg_per_sec
        self.okr_spatial_frequency_deg = okr_spatial_frequency_deg
        self.okr_speed_deg_per_sec = okr_speed_deg_per_sec
        self.looming_center_mm = looming_center_mm
        self.looming_period_sec = looming_period_sec
        self.looming_expansion_time_sec = looming_expansion_time_sec
        self.looming_expansion_speed_mm_per_sec = looming_expansion_speed_mm_per_sec

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

        self.cmb_stim_select = QComboBox()
        self.cmb_stim_select.addItem('Dark')
        self.cmb_stim_select.addItem('Bright')
        self.cmb_stim_select.addItem('Phototaxis')
        self.cmb_stim_select.addItem('OMR')
        self.cmb_stim_select.addItem('OKR')
        self.cmb_stim_select.addItem('Looming')
        self.cmb_stim_select.currentIndexChanged.connect(self.stim_changed)

        # Phototaxis
        self.chb_phototaxis_polarity = QCheckBox('invert polarity', self.window)
        self.chb_phototaxis_polarity.stateChanged.connect(self.on_change)
        self.chb_phototaxis_polarity.setChecked(self.phototaxis_polarity==1)

        # OMR
        self.sb_omr_spatial_freq = LabeledDoubleSpinBox()
        self.sb_omr_spatial_freq.setText('Spatial frequency (deg)')
        self.sb_omr_spatial_freq.setRange(0,10_000)
        self.sb_omr_spatial_freq.setValue(self.omr_spatial_frequency_deg)
        self.sb_omr_spatial_freq.valueChanged.connect(self.on_change)

        self.sb_omr_angle = LabeledDoubleSpinBox()
        self.sb_omr_angle.setText('Grating angle (deg)')
        self.sb_omr_angle.setRange(0,360)
        self.sb_omr_angle.setValue(self.omr_angle_deg)
        self.sb_omr_angle.valueChanged.connect(self.on_change)

        self.sb_omr_speed = LabeledDoubleSpinBox()
        self.sb_omr_speed.setText('Grating speed (deg/s)')
        self.sb_omr_speed.setRange(-10_000,10_000)
        self.sb_omr_speed.setValue(self.omr_speed_deg_per_sec)
        self.sb_omr_speed.valueChanged.connect(self.on_change)

        # OKR
        self.sb_okr_spatial_freq = LabeledDoubleSpinBox()
        self.sb_okr_spatial_freq.setText('Spatial frequence (deg)')
        self.sb_okr_spatial_freq.setRange(0,10_000)
        self.sb_okr_spatial_freq.setValue(self.okr_spatial_frequency_deg)
        self.sb_okr_spatial_freq.valueChanged.connect(self.on_change)

        self.sb_okr_speed = LabeledDoubleSpinBox()
        self.sb_okr_speed.setText('speed (deg/s)')
        self.sb_okr_speed.setRange(-10_000,10_000)
        self.sb_okr_speed.setValue(self.okr_speed_deg_per_sec)
        self.sb_okr_speed.valueChanged.connect(self.on_change)

        # Looming
        self.sb_looming_center_mm_x = LabeledDoubleSpinBox()
        self.sb_looming_center_mm_x.setText('X (mm)')
        self.sb_looming_center_mm_x.setRange(-10_000,10_000)
        self.sb_looming_center_mm_x.setValue(self.looming_center_mm[0])
        self.sb_looming_center_mm_x.valueChanged.connect(self.on_change)

        self.sb_looming_center_mm_y = LabeledDoubleSpinBox()
        self.sb_looming_center_mm_y.setText('Y (mm)')
        self.sb_looming_center_mm_y.setRange(-10_000,10_000)
        self.sb_looming_center_mm_y.setValue(self.looming_center_mm[1])
        self.sb_looming_center_mm_y.valueChanged.connect(self.on_change)

        self.sb_looming_period_sec = LabeledDoubleSpinBox()
        self.sb_looming_period_sec.setText('period (s)')
        self.sb_looming_period_sec.setRange(0,100_000)
        self.sb_looming_period_sec.setValue(self.looming_period_sec)
        self.sb_looming_period_sec.valueChanged.connect(self.on_change)

        self.sb_looming_expansion_time_sec = LabeledDoubleSpinBox()
        self.sb_looming_expansion_time_sec.setText('expansion time (s)')
        self.sb_looming_expansion_time_sec.setRange(0,100_000)
        self.sb_looming_expansion_time_sec.setValue(self.looming_expansion_time_sec)
        self.sb_looming_expansion_time_sec.valueChanged.connect(self.on_change)

        self.sb_looming_expansion_speed_mm_per_sec = LabeledDoubleSpinBox()
        self.sb_looming_expansion_speed_mm_per_sec.setText('expansion speed (mm/s)')
        self.sb_looming_expansion_speed_mm_per_sec.setRange(0,100_000)
        self.sb_looming_expansion_speed_mm_per_sec.setValue(self.looming_expansion_speed_mm_per_sec)
        self.sb_looming_expansion_speed_mm_per_sec.valueChanged.connect(self.on_change)

    def layout_components(self):

        phototaxis_layout = QVBoxLayout()
        phototaxis_layout.addWidget(self.chb_phototaxis_polarity)
        self.phototaxis_group = QGroupBox('Phototaxis parameters')
        self.phototaxis_group.setLayout(phototaxis_layout)

        omr_layout = QVBoxLayout()
        omr_layout.addWidget(self.sb_omr_spatial_freq)
        omr_layout.addWidget(self.sb_omr_angle)
        omr_layout.addWidget(self.sb_omr_speed)
        self.omr_group = QGroupBox('OMR parameters')
        self.omr_group.setLayout(omr_layout)

        okr_layout = QVBoxLayout()
        okr_layout.addWidget(self.sb_okr_spatial_freq)
        okr_layout.addWidget(self.sb_okr_speed)
        self.okr_group = QGroupBox('OKR parameters')
        self.okr_group.setLayout(okr_layout)

        looming_layout = QVBoxLayout()
        looming_layout.addWidget(self.sb_looming_center_mm_x)
        looming_layout.addWidget(self.sb_looming_center_mm_y)
        looming_layout.addWidget(self.sb_looming_period_sec)
        looming_layout.addWidget(self.sb_looming_expansion_time_sec)
        looming_layout.addWidget(self.sb_looming_expansion_speed_mm_per_sec)
        self.looming_group = QGroupBox('Looming parameters')
        self.looming_group.setLayout(looming_layout)

        self.stack = QStackedWidget()
        self.stack.addWidget(QLabel())
        self.stack.addWidget(QLabel())
        self.stack.addWidget(self.phototaxis_group)
        self.stack.addWidget(self.omr_group)
        self.stack.addWidget(self.okr_group)
        self.stack.addWidget(self.looming_group)
    
        layout = QVBoxLayout(self.window)
        layout.addWidget(self.cmb_stim_select)
        layout.addWidget(self.stack)

    def stim_changed(self):
        self.stack.setCurrentIndex(self.cmb_stim_select.currentIndex())
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
            res['visual_stim_control']['stim_select'] = self.cmb_stim_select.currentIndex()
            res['visual_stim_control']['phototaxis_polarity'] = -1+2*self.chb_phototaxis_polarity.isChecked()
            res['visual_stim_control']['omr_spatial_frequency_deg'] = self.sb_omr_spatial_freq.value() 
            res['visual_stim_control']['omr_angle_deg'] = self.sb_omr_angle.value()
            res['visual_stim_control']['omr_speed_deg_per_sec'] = self.sb_omr_speed.value() 
            res['visual_stim_control']['okr_spatial_frequency_deg'] = self.sb_okr_spatial_freq.value()
            res['visual_stim_control']['okr_speed_deg_per_sec'] = self.sb_okr_speed.value()
            res['visual_stim_control']['looming_center_mm_x'] = self.sb_looming_center_mm_x.value()
            res['visual_stim_control']['looming_center_mm_y'] = self.sb_looming_center_mm_y.value()
            res['visual_stim_control']['looming_period_sec'] = self.sb_looming_period_sec.value()
            res['visual_stim_control']['looming_expansion_time_sec'] = self.sb_looming_expansion_time_sec.value()
            res['visual_stim_control']['looming_expansion_speed_mm_per_sec'] = self.sb_looming_expansion_speed_mm_per_sec.value()
            self.updated = False
            return res       
        else:
            return None
        