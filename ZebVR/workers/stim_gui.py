from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional, Tuple
from qt_widgets import LabeledDoubleSpinBox
import time

from PyQt5.QtWidgets import (
    QApplication, 
    QWidget, 
    QCheckBox, 
    QStackedWidget, 
    QGroupBox, 
    QHBoxLayout,
    QVBoxLayout, 
    QComboBox,
    QLabel
)

class StimWidget(QWidget):

    def __init__(
            self, 
            phototaxis_polarity: int = 1,
            omr_spatial_period_mm: float = 20,
            omr_angle_deg: float = 0,
            omr_speed_mm_per_sec: float = 360,
            okr_spatial_frequency_deg: float = 45,
            okr_speed_deg_per_sec: float = 60,
            looming_center_mm: Tuple = (1,1),
            looming_period_sec: float = 30,
            looming_expansion_time_sec: float = 3,
            looming_expansion_speed_mm_per_sec: float = 10,
            foreground_color: Tuple = (1.0, 1.0, 1.0, 1.0),
            background_color: Tuple = (0.0, 0.0, 0.0, 1.0),
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)

        self.phototaxis_polarity = phototaxis_polarity
        self.omr_spatial_period_mm = omr_spatial_period_mm
        self.omr_angle_deg = omr_angle_deg
        self.omr_speed_mm_per_sec = omr_speed_mm_per_sec
        self.okr_spatial_frequency_deg = okr_spatial_frequency_deg
        self.okr_speed_deg_per_sec = okr_speed_deg_per_sec
        self.looming_center_mm = looming_center_mm
        self.looming_period_sec = looming_period_sec
        self.looming_expansion_time_sec = looming_expansion_time_sec
        self.looming_expansion_speed_mm_per_sec = looming_expansion_speed_mm_per_sec
        self.foreground_color = foreground_color
        self.background_color = background_color
        
        self.updated = False
        self.declare_components()
        self.layout_components()
        self.setWindowTitle('Visual stim controls')

    def declare_components(self):

        self.cmb_stim_select = QComboBox()
        self.cmb_stim_select.addItem('Dark')
        self.cmb_stim_select.addItem('Bright')
        self.cmb_stim_select.addItem('Phototaxis')
        self.cmb_stim_select.addItem('OMR')
        self.cmb_stim_select.addItem('OKR')
        self.cmb_stim_select.addItem('Looming')
        self.cmb_stim_select.currentIndexChanged.connect(self.stim_changed)

        # Colors
        self.lbl_foreground_color = QLabel('Foreground color:')

        self.sb_foreground_color_R = LabeledDoubleSpinBox()
        self.sb_foreground_color_R.setText('R')
        self.sb_foreground_color_R.setRange(0,1)
        self.sb_foreground_color_R.setSingleStep(0.05)
        self.sb_foreground_color_R.setValue(self.foreground_color[0])
        self.sb_foreground_color_R.valueChanged.connect(self.on_change)

        self.sb_foreground_color_G = LabeledDoubleSpinBox()
        self.sb_foreground_color_G.setText('G')
        self.sb_foreground_color_G.setRange(0,1)
        self.sb_foreground_color_G.setSingleStep(0.05)
        self.sb_foreground_color_G.setValue(self.foreground_color[1])
        self.sb_foreground_color_G.valueChanged.connect(self.on_change)

        self.sb_foreground_color_B = LabeledDoubleSpinBox()
        self.sb_foreground_color_B.setText('B')
        self.sb_foreground_color_B.setRange(0,1)
        self.sb_foreground_color_B.setSingleStep(0.05)
        self.sb_foreground_color_B.setValue(self.foreground_color[2])
        self.sb_foreground_color_B.valueChanged.connect(self.on_change)

        self.sb_foreground_color_A = LabeledDoubleSpinBox()
        self.sb_foreground_color_A.setText('A')
        self.sb_foreground_color_A.setRange(0,1)
        self.sb_foreground_color_A.setSingleStep(0.05)
        self.sb_foreground_color_A.setValue(self.foreground_color[3])
        self.sb_foreground_color_A.valueChanged.connect(self.on_change)

        self.lbl_background_color = QLabel('Background color:')

        self.sb_background_color_R = LabeledDoubleSpinBox()
        self.sb_background_color_R.setText('R')
        self.sb_background_color_R.setRange(0,1)
        self.sb_background_color_R.setSingleStep(0.05)
        self.sb_background_color_R.setValue(self.background_color[0])
        self.sb_background_color_R.valueChanged.connect(self.on_change)

        self.sb_background_color_G = LabeledDoubleSpinBox()
        self.sb_background_color_G.setText('G')
        self.sb_background_color_G.setRange(0,1)
        self.sb_background_color_G.setSingleStep(0.05)
        self.sb_background_color_G.setValue(self.background_color[1])
        self.sb_background_color_G.valueChanged.connect(self.on_change)

        self.sb_background_color_B = LabeledDoubleSpinBox()
        self.sb_background_color_B.setText('B')
        self.sb_background_color_B.setRange(0,1)
        self.sb_background_color_B.setSingleStep(0.05)
        self.sb_background_color_B.setValue(self.background_color[2])
        self.sb_background_color_B.valueChanged.connect(self.on_change)

        self.sb_background_color_A = LabeledDoubleSpinBox()
        self.sb_background_color_A.setText('A')
        self.sb_background_color_A.setRange(0,1)
        self.sb_background_color_A.setSingleStep(0.05)
        self.sb_background_color_A.setValue(self.background_color[3])
        self.sb_background_color_A.valueChanged.connect(self.on_change)

        # Phototaxis
        self.chb_phototaxis_polarity = QCheckBox('invert polarity')
        self.chb_phototaxis_polarity.stateChanged.connect(self.on_change)
        self.chb_phototaxis_polarity.setChecked(self.phototaxis_polarity==1)

        # OMR
        self.sb_omr_spatial_freq = LabeledDoubleSpinBox()
        self.sb_omr_spatial_freq.setText('Spatial period (mm)')
        self.sb_omr_spatial_freq.setRange(0,10_000)
        self.sb_omr_spatial_freq.setValue(self.omr_spatial_period_mm)
        self.sb_omr_spatial_freq.valueChanged.connect(self.on_change)

        self.sb_omr_angle = LabeledDoubleSpinBox()
        self.sb_omr_angle.setText('Grating angle (deg)')
        self.sb_omr_angle.setRange(-180,180)
        self.sb_omr_angle.setValue(self.omr_angle_deg)
        self.sb_omr_angle.valueChanged.connect(self.on_change)

        self.sb_omr_speed = LabeledDoubleSpinBox()
        self.sb_omr_speed.setText('Grating speed (mm/s)')
        self.sb_omr_speed.setRange(-10_000,10_000)
        self.sb_omr_speed.setValue(self.omr_speed_mm_per_sec)
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

        foreground_color_layout = QHBoxLayout()
        foreground_color_layout.addWidget(self.lbl_foreground_color)
        foreground_color_layout.addWidget(self.sb_foreground_color_R)
        foreground_color_layout.addWidget(self.sb_foreground_color_G)
        foreground_color_layout.addWidget(self.sb_foreground_color_B)
        foreground_color_layout.addWidget(self.sb_foreground_color_A)

        background_color_layout = QHBoxLayout()
        background_color_layout.addWidget(self.lbl_background_color)
        background_color_layout.addWidget(self.sb_background_color_R)
        background_color_layout.addWidget(self.sb_background_color_G)
        background_color_layout.addWidget(self.sb_background_color_B)
        background_color_layout.addWidget(self.sb_background_color_A)

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
    
        layout = QVBoxLayout(self)
        layout.addWidget(self.cmb_stim_select)
        layout.addLayout(foreground_color_layout)
        layout.addLayout(background_color_layout)
        layout.addWidget(self.stack)

    def stim_changed(self):
        self.stack.setCurrentIndex(self.cmb_stim_select.currentIndex())
        self.on_change()

    def on_change(self):
        self.updated = True

    def is_updated(self) -> bool:
        return self.updated
    
    def set_updated(self, updated:bool) -> None:
        self.updated = updated

    def get_state(self) -> Dict:
        state = {}
        state['stim_select'] = self.cmb_stim_select.currentIndex()
        state['phototaxis_polarity'] = -1+2*self.chb_phototaxis_polarity.isChecked()
        state['omr_spatial_period_mm'] = self.sb_omr_spatial_freq.value()
        state['omr_angle_deg'] = self.sb_omr_angle.value()
        state['omr_speed_mm_per_sec'] = self.sb_omr_speed.value() 
        state['okr_spatial_frequency_deg'] = self.sb_okr_spatial_freq.value()
        state['okr_speed_deg_per_sec'] = self.sb_okr_speed.value()
        state['looming_center_mm_x'] = self.sb_looming_center_mm_x.value()
        state['looming_center_mm_y'] = self.sb_looming_center_mm_y.value()
        state['looming_period_sec'] = self.sb_looming_period_sec.value()
        state['looming_expansion_time_sec'] = self.sb_looming_expansion_time_sec.value()
        state['looming_expansion_speed_mm_per_sec'] = self.sb_looming_expansion_speed_mm_per_sec.value()
        state['foreground_color_R'] = self.sb_foreground_color_R.value()
        state['foreground_color_G'] = self.sb_foreground_color_G.value()
        state['foreground_color_B'] = self.sb_foreground_color_B.value()
        state['foreground_color_A'] = self.sb_foreground_color_A.value()
        state['background_color_R'] = self.sb_background_color_R.value()
        state['background_color_G'] = self.sb_background_color_G.value()
        state['background_color_B'] = self.sb_background_color_B.value()
        state['background_color_A'] = self.sb_background_color_A.value()
        return state

class StimGUI(WorkerNode):

    def __init__(
            self, 
            phototaxis_polarity: int = 1,
            omr_spatial_period_mm: float = 20,
            omr_angle_deg: float = 0,
            omr_speed_mm_per_sec: float = 360,
            okr_spatial_frequency_deg: float = 45,
            okr_speed_deg_per_sec: float = 60,
            looming_center_mm: Tuple = (1,1),
            looming_period_sec: float = 30,
            looming_expansion_time_sec: float = 3,
            looming_expansion_speed_mm_per_sec: float = 10,
            foreground_color: Tuple = (1.0, 1.0, 1.0, 1.0),
            background_color: Tuple = (0.0, 0.0, 0.0, 1.0),
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)

        self.phototaxis_polarity = phototaxis_polarity
        self.omr_spatial_period_mm = omr_spatial_period_mm
        self.omr_angle_deg = omr_angle_deg
        self.omr_speed_mm_per_sec = omr_speed_mm_per_sec
        self.okr_spatial_frequency_deg = okr_spatial_frequency_deg
        self.okr_speed_deg_per_sec = okr_speed_deg_per_sec
        self.looming_center_mm = looming_center_mm
        self.looming_period_sec = looming_period_sec
        self.looming_expansion_time_sec = looming_expansion_time_sec
        self.looming_expansion_speed_mm_per_sec = looming_expansion_speed_mm_per_sec
        self.foreground_color = foreground_color
        self.background_color = background_color

    def initialize(self) -> None:
        super().initialize()
        self.app = QApplication([])
        self.window = StimWidget(
            phototaxis_polarity=self.phototaxis_polarity,
            omr_spatial_period_mm=self.omr_spatial_period_mm,
            omr_angle_deg=self.omr_angle_deg,
            omr_speed_mm_per_sec=self.omr_speed_mm_per_sec,
            okr_spatial_frequency_deg=self.okr_spatial_frequency_deg,
            okr_speed_deg_per_sec=self.okr_speed_deg_per_sec,
            looming_center_mm=self.looming_center_mm,
            looming_period_sec=self.looming_period_sec,
            looming_expansion_time_sec=self.looming_expansion_time_sec,
            looming_expansion_speed_mm_per_sec=self.looming_expansion_speed_mm_per_sec,
            foreground_color=self.foreground_color,
            background_color=self.background_color
        )
        self.window.show()
    
    def process_data(self, data: None) -> NDArray:
        self.app.processEvents()
        self.app.sendPostedEvents()
        time.sleep(0.01)

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        # send only one message when things are changed
        if self.window.is_updated():
            res = {}
            res['visual_stim_control'] = self.window.get_state()
            self.window.set_updated(False)
            return res       
        else:
            return None
        