from typing import Dict, Tuple
from qt_widgets import LabeledDoubleSpinBox, LabeledSpinBox

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, 
    QCheckBox, 
    QStackedWidget, 
    QGroupBox, 
    QHBoxLayout,
    QVBoxLayout, 
    QComboBox,
    QLabel
)

from ..protocol import Stim, TriggerPolarity

class TriggerWidget(QWidget):

    state_changed = pyqtSignal()
    
    def __init__(
            self, 
            *args, 
            **kwargs
        ):
        
        super().__init__(*args, **kwargs)
        
        self.updated = False
        self.declare_components()
        self.layout_components()

    def declare_components(self):

        self.cmb_trigger_select = QComboBox()
        self.cmb_trigger_select.addItem('Software')
        self.cmb_trigger_select.addItem('Tracking')
        self.cmb_trigger_select.currentIndexChanged.connect(self.trigger_changed)

        self.cmb_trigger_polarity = QComboBox()
        for pol in TriggerPolarity:
            self.cmb_trigger_polarity.addItem(str(pol))

        self.ROI_x = LabeledSpinBox()
        self.ROI_x.setText('x')
        self.ROI_x.setRange(0, 10_000) # TODO fix that
        self.ROI_x.setValue(0)
        self.ROI_x.valueChanged.connect(self.on_change)

        self.ROI_y = LabeledSpinBox()
        self.ROI_y.setText('y')
        self.ROI_y.setRange(0, 10_000) # TODO fix that
        self.ROI_y.setValue(0)
        self.ROI_y.valueChanged.connect(self.on_change)

        self.ROI_h = LabeledSpinBox()
        self.ROI_h.setText('h')
        self.ROI_h.setRange(0, 10_000) # TODO fix that
        self.ROI_h.setValue(0)
        self.ROI_h.valueChanged.connect(self.on_change)

        self.ROI_w = LabeledSpinBox()
        self.ROI_w.setText('w')
        self.ROI_w.setRange(0, 10_000) # TODO fix that
        self.ROI_w.setValue(0)
        self.ROI_w.valueChanged.connect(self.on_change)

    def layout_components(self):

        software_trigger_layout = QVBoxLayout()
        software_trigger_layout.addStretch()
        self.software_trigger_group = QGroupBox('Sotware Trigger parameters')
        self.software_trigger_group.setLayout(software_trigger_layout)

        tracking_trigger_layout = QVBoxLayout()
        tracking_trigger_layout.addWidget(self.ROI_x)
        tracking_trigger_layout.addWidget(self.ROI_y)
        tracking_trigger_layout.addWidget(self.ROI_h)
        tracking_trigger_layout.addWidget(self.ROI_w)
        tracking_trigger_layout.addStretch()
        self.tracking_trigger_group = QGroupBox('Tracking Trigger parameters')
        self.tracking_trigger_group.setLayout(tracking_trigger_layout)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.software_trigger_group)
        self.stack.addWidget(self.tracking_trigger_group)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.cmb_trigger_select)
        layout.addWidget(self.cmb_trigger_polarity)
        layout.addWidget(self.stack)

    def trigger_changed(self):
        self.stack.setCurrentIndex(self.cmb_trigger_select.currentIndex())
        self.on_change()

    def on_change(self):
        self.updated = True
        self.state_changed.emit()

    def is_updated(self) -> bool:
        return self.updated
    
    def set_updated(self, updated:bool) -> None:
        self.updated = updated

    def get_state(self) -> Dict:
        state = {}
        state['trigger_select'] = self.cmb_trigger_select.currentIndex()
        state['trigger_polarity'] = self.cmb_trigger_polarity.currentIndex()
        state['ROI_x'] = self.ROI_x.value()
        state['ROI_y'] = self.ROI_y.value()
        state['ROI_h'] = self.ROI_h.value()
        state['ROI_w'] = self.ROI_w.value()
        return state

class StimWidget(QWidget):

    state_changed = pyqtSignal()

    def __init__(
            self, 
            phototaxis_polarity: int = 1,
            omr_spatial_period_mm: float = 5,
            omr_angle_deg: float = 0,
            omr_speed_mm_per_sec: float = 10,
            okr_spatial_frequency_deg: float = 20,
            okr_speed_deg_per_sec: float = 36,
            looming_center_mm: Tuple = (15,15),
            looming_period_sec: float = 30,
            looming_expansion_time_sec: float = 10,
            looming_expansion_speed_mm_per_sec: float = 10,
            foreground_color: Tuple = (0.2, 0.2, 0.2, 1.0),
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
        for stim in Stim:
            self.cmb_stim_select.addItem(str(stim))
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
        phototaxis_layout.addStretch()
        self.phototaxis_group = QGroupBox('Phototaxis parameters')
        self.phototaxis_group.setLayout(phototaxis_layout)

        omr_layout = QVBoxLayout()
        omr_layout.addWidget(self.sb_omr_spatial_freq)
        omr_layout.addWidget(self.sb_omr_angle)
        omr_layout.addWidget(self.sb_omr_speed)
        omr_layout.addStretch()
        self.omr_group = QGroupBox('OMR parameters')
        self.omr_group.setLayout(omr_layout)

        okr_layout = QVBoxLayout()
        okr_layout.addWidget(self.sb_okr_spatial_freq)
        okr_layout.addWidget(self.sb_okr_speed)
        okr_layout.addStretch()
        self.okr_group = QGroupBox('OKR parameters')
        self.okr_group.setLayout(okr_layout)

        looming_layout = QVBoxLayout()
        looming_layout.addWidget(self.sb_looming_center_mm_x)
        looming_layout.addWidget(self.sb_looming_center_mm_y)
        looming_layout.addWidget(self.sb_looming_period_sec)
        looming_layout.addWidget(self.sb_looming_expansion_time_sec)
        looming_layout.addWidget(self.sb_looming_expansion_speed_mm_per_sec)
        looming_layout.addStretch()
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
        self.state_changed.emit()

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
        state['looming_center_mm'] = (
            self.sb_looming_center_mm_x.value(),
            self.sb_looming_center_mm_y.value()
        )
        state['looming_period_sec'] = self.sb_looming_period_sec.value()
        state['looming_expansion_time_sec'] = self.sb_looming_expansion_time_sec.value()
        state['looming_expansion_speed_mm_per_sec'] = self.sb_looming_expansion_speed_mm_per_sec.value()
        state['foreground_color'] = (
            self.sb_foreground_color_R.value(),
            self.sb_foreground_color_G.value(),
            self.sb_foreground_color_B.value(),
            self.sb_foreground_color_A.value()
        )
        state['background_color'] = (
            self.sb_background_color_R.value(),
            self.sb_background_color_G.value(),
            self.sb_background_color_B.value(),
            self.sb_background_color_A.value()
        )
        return state
