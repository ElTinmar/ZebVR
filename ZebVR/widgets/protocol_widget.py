from typing import Dict, Tuple
import numpy as np

from qt_widgets import LabeledDoubleSpinBox, LabeledSpinBox, FileOpenLabeledEditButton

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, 
    QCheckBox, 
    QStackedWidget, 
    QGroupBox, 
    QHBoxLayout,
    QVBoxLayout, 
    QComboBox,
    QLabel,
    QPushButton,
    QStackedLayout
)
from ..protocol import (
    Stim,
    StopPolicy,
    TriggerType,
    TriggerPolarity,
    ProtocolItem,
    Phototaxis,
    OKR,
    OMR,
    Dark,
    Bright,
    Looming,
    Pause,
    SoftwareTrigger,
    TrackingTrigger
)
class StopWidget(QWidget):

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

        self.cmb_policy_select = QComboBox()
        for policy in StopPolicy:
            self.cmb_policy_select.addItem(str(policy))
        self.cmb_policy_select.currentIndexChanged.connect(self.policy_changed)

        self.pause_sec = LabeledDoubleSpinBox()
        self.pause_sec.setText('pause (sec):')
        self.pause_sec.setRange(0,100_000)
        self.pause_sec.setSingleStep(0.5)
        self.pause_sec.setValue(0)
        self.pause_sec.editingFinished.connect(self.on_change)

        self.cmb_trigger_select = QComboBox()
        for trigger in TriggerType:
            self.cmb_trigger_select.addItem(str(trigger))
        self.cmb_trigger_select.currentIndexChanged.connect(self.trigger_changed)

        self.cmb_trigger_polarity = QComboBox()
        for pol in TriggerPolarity:
            self.cmb_trigger_polarity.addItem(str(pol))

        self.debouncer = LabeledSpinBox()
        self.debouncer.setText('debouncer frames')
        self.debouncer.setRange(0, 100) 
        self.debouncer.setValue(5)
        self.debouncer.valueChanged.connect(self.on_change)

        self.trigger_mask = FileOpenLabeledEditButton()
        self.trigger_mask.setLabel('laod mask:')

        self.trigger_mask_button = QPushButton('draw mask')
        self.trigger_mask_button.clicked.connect(self.draw_trigger_mask)

    def draw_trigger_mask(self):
        pass

    def layout_components(self):

        software_trigger_layout = QVBoxLayout()
        software_trigger_layout.addStretch()
        self.software_trigger_group = QGroupBox('Sotware Trigger parameters')
        self.software_trigger_group.setLayout(software_trigger_layout)

        ttl_trigger_layout = QVBoxLayout()
        ttl_trigger_layout.addStretch()
        self.ttl_trigger_group = QGroupBox('TTL Trigger parameters')
        self.ttl_trigger_group.setLayout(ttl_trigger_layout)

        tracking_trigger_layout = QVBoxLayout()
        tracking_trigger_layout.addWidget(self.trigger_mask)
        tracking_trigger_layout.addWidget(self.trigger_mask_button)
        tracking_trigger_layout.addStretch()
        self.tracking_trigger_group = QGroupBox('Tracking Trigger parameters')
        self.tracking_trigger_group.setLayout(tracking_trigger_layout)

        self.trigger_stack = QStackedWidget()
        self.trigger_stack.addWidget(self.software_trigger_group)
        self.trigger_stack.addWidget(self.ttl_trigger_group)
        self.trigger_stack.addWidget(self.tracking_trigger_group)

        trigger_container = QWidget()
        trigger_layout = QVBoxLayout(trigger_container)
        trigger_layout.addWidget(self.cmb_trigger_select)
        trigger_layout.addWidget(self.cmb_trigger_polarity)
        trigger_layout.addWidget(self.debouncer)
        trigger_layout.addWidget(self.trigger_stack)
            
        self.policy_stack = QStackedWidget()
        self.policy_stack.addWidget(self.pause_sec)
        self.policy_stack.addWidget(trigger_container)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.cmb_policy_select)
        main_layout.addWidget(self.policy_stack)

    def policy_changed(self):
        self.policy_stack.setCurrentIndex(self.cmb_policy_select.currentIndex())
        self.on_change()

    def trigger_changed(self):
        self.trigger_stack.setCurrentIndex(self.cmb_trigger_select.currentIndex())
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
        state['stop_policy'] = self.cmb_policy_select.currentIndex()
        state['trigger_select'] = self.cmb_trigger_select.currentIndex()
        state['trigger_polarity'] = self.cmb_trigger_polarity.currentIndex()
        state['debouncer'] = self.debouncer.value()
        state['trigger_mask'] = self.trigger_mask.text()
        state['pause_sec'] = self.pause_sec.value()
        return state

# TODO check if this can be simplified (maybe set_state/get_state)
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
        
        # TODO add stuff for acoustic and other types of stim 

        self.cmb_stim_select = QComboBox()
        for stim in Stim.Visual:
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

        # Stop condition
        self.stop_condition = StopWidget()

    def layout_components(self):

        foreground_color_layout = QHBoxLayout()
        foreground_color_layout.addWidget(self.lbl_foreground_color)
        foreground_color_layout.addWidget(self.sb_foreground_color_R)
        foreground_color_layout.addWidget(self.sb_foreground_color_G)
        foreground_color_layout.addWidget(self.sb_foreground_color_B)
        foreground_color_layout.addWidget(self.sb_foreground_color_A)
        foreground_color_layout.addStretch()

        background_color_layout = QHBoxLayout()
        background_color_layout.addWidget(self.lbl_background_color)
        background_color_layout.addWidget(self.sb_background_color_R)
        background_color_layout.addWidget(self.sb_background_color_G)
        background_color_layout.addWidget(self.sb_background_color_B)
        background_color_layout.addWidget(self.sb_background_color_A)
        background_color_layout.addStretch()

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
        layout.addWidget(self.stop_condition)

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
        state['stop_condition'] = self.stop_condition.get_state()
        return state

    def set_protocol_item(self, item: ProtocolItem):
        # set StimWidget value based on provided ProtocolItem   

        self.sb_foreground_color_R.setValue(item.foreground_color[0])
        self.sb_foreground_color_G.setValue(item.foreground_color[1])
        self.sb_foreground_color_B.setValue(item.foreground_color[2])
        self.sb_foreground_color_A.setValue(item.foreground_color[3])
        
        self.sb_background_color_R.setValue(item.background_color[0])
        self.sb_background_color_G.setValue(item.background_color[1])
        self.sb_background_color_B.setValue(item.background_color[2])
        self.sb_background_color_A.setValue(item.background_color[3])         
        
        if isinstance(item, Bright):
            self.cmb_stim_select.setCurrentText(str(Stim.Visual.BRIGHT))

        elif isinstance(item, Dark):
            self.cmb_stim_select.setCurrentText(str(Stim.Visual.DARK))

        elif isinstance(item, Phototaxis):
            self.cmb_stim_select.setCurrentText(str(Stim.Visual.PHOTOTAXIS))
            self.chb_phototaxis_polarity.setChecked(item.phototaxis_polarity == 1) 

        elif isinstance(item, OMR):
            self.cmb_stim_select.setCurrentText(str(Stim.Visual.OMR))
            self.sb_omr_spatial_freq.setValue(item.omr_spatial_period_mm)
            self.sb_omr_angle.setValue(item.omr_angle_deg)
            self.sb_omr_speed.setValue(item.omr_speed_mm_per_sec)  
    
        elif isinstance(item, OKR):
            self.cmb_stim_select.setCurrentText(str(Stim.Visual.OKR))
            self.sb_okr_spatial_freq.setValue(item.okr_spatial_frequency_deg)
            self.sb_okr_speed.setValue(item.okr_speed_deg_per_sec) 
    
        elif isinstance(item, Looming):
            self.cmb_stim_select.setCurrentText(str(Stim.Visual.LOOMING))
            self.sb_looming_center_mm_x.setValue(item.looming_center_mm[0])
            self.sb_looming_center_mm_y.setValue(item.looming_center_mm[1])
            self.sb_looming_period_sec.setValue(item.looming_period_sec)
            self.sb_looming_expansion_time_sec.setValue(item.looming_expansion_time_sec)
            self.sb_looming_expansion_speed_mm_per_sec.setValue(item.looming_expansion_speed_mm_per_sec)

    def get_protocol_item(self) -> ProtocolItem:

        state = self.get_state()

        stop_condition = None

        if state['stop_condition']['stop_policy'] == StopPolicy.PAUSE:
            stop_condition = Pause(state['stop_condition']['pause_sec'])

        if state['stop_condition']['stop_policy'] == StopPolicy.TRIGGER:

            if state['stop_condition']['trigger_select'] == TriggerType.SOFTWARE:
                stop_condition = SoftwareTrigger(
                    polarity = TriggerPolarity(state['stop_condition']['trigger_polarity']),
                    debouncer_length = state['stop_condition']['debouncer']
                )

            if state['stop_condition']['trigger_select'] == TriggerType.TTL:
                pass

            if state['stop_condition']['trigger_select'] == TriggerType.TRACKING:
                with open(state['stop_condition']['trigger_mask'], 'rb') as f:
                    trigger_mask = np.load(f)

                stop_condition = TrackingTrigger(
                    trigger_mask = trigger_mask,
                    polarity = TriggerPolarity(state['stop_condition']['trigger_polarity']),
                    debouncer_length = state['stop_condition']['debouncer']
                )

        protocol = None
        if state['stim_select'] == Stim.Visual.DARK:

            protocol = Dark(
                foreground_color = (
                    self.sb_foreground_color_R.value(), 
                    self.sb_foreground_color_G.value(),
                    self.sb_foreground_color_B.value(),
                    self.sb_foreground_color_A.value()
                ),
                background_color = (
                    self.sb_background_color_R.value(), 
                    self.sb_background_color_G.value(),
                    self.sb_background_color_B.value(),
                    self.sb_background_color_A.value()
                ),
                stop_condition = stop_condition
            )

        if state['stim_select'] == Stim.Visual.BRIGHT:
            protocol = Bright(
                foreground_color = (
                    self.sb_foreground_color_R.value(), 
                    self.sb_foreground_color_G.value(),
                    self.sb_foreground_color_B.value(),
                    self.sb_foreground_color_A.value()
                ),
                background_color = (
                    self.sb_background_color_R.value(), 
                    self.sb_background_color_G.value(),
                    self.sb_background_color_B.value(),
                    self.sb_background_color_A.value()
                ),
                stop_condition = stop_condition
            )

        if state['stim_select'] == Stim.Visual.PHOTOTAXIS:
            protocol = Phototaxis(
                foreground_color = (
                    self.sb_foreground_color_R.value(), 
                    self.sb_foreground_color_G.value(),
                    self.sb_foreground_color_B.value(),
                    self.sb_foreground_color_A.value()
                ),
                background_color = (
                    self.sb_background_color_R.value(), 
                    self.sb_background_color_G.value(),
                    self.sb_background_color_B.value(),
                    self.sb_background_color_A.value()
                ),
                phototaxis_polarity=-1+2*self.chb_phototaxis_polarity.isChecked(),
                stop_condition = stop_condition
            )

        if state['stim_select'] == Stim.Visual.OMR:
            protocol = OMR(
                foreground_color = (
                    self.sb_foreground_color_R.value(), 
                    self.sb_foreground_color_G.value(),
                    self.sb_foreground_color_B.value(),
                    self.sb_foreground_color_A.value()
                ),
                background_color = (
                    self.sb_background_color_R.value(), 
                    self.sb_background_color_G.value(),
                    self.sb_background_color_B.value(),
                    self.sb_background_color_A.value()
                ),
                omr_spatial_period_mm = self.sb_omr_spatial_freq.value(),
                omr_angle_deg =self.sb_omr_angle.value(),
                omr_speed_mm_per_sec = self.sb_omr_speed.value(),
                stop_condition = stop_condition
            )

        if state['stim_select'] == Stim.Visual.OKR:
            protocol = OKR(
                foreground_color = (
                    self.sb_foreground_color_R.value(), 
                    self.sb_foreground_color_G.value(),
                    self.sb_foreground_color_B.value(),
                    self.sb_foreground_color_A.value()
                ),
                background_color = (
                    self.sb_background_color_R.value(), 
                    self.sb_background_color_G.value(),
                    self.sb_background_color_B.value(),
                    self.sb_background_color_A.value()
                ),
                okr_spatial_frequency_deg = self.sb_okr_spatial_freq.value(),
                okr_speed_deg_per_sec = self.sb_okr_speed.value(),
                stop_condition = stop_condition
            )

        if state['stim_select'] == Stim.Visual.LOOMING:
            protocol = Looming(
                foreground_color = (
                    self.sb_foreground_color_R.value(), 
                    self.sb_foreground_color_G.value(),
                    self.sb_foreground_color_B.value(),
                    self.sb_foreground_color_A.value()
                ),
                background_color = (
                    self.sb_background_color_R.value(), 
                    self.sb_background_color_G.value(),
                    self.sb_background_color_B.value(),
                    self.sb_background_color_A.value()
                ),
                looming_center_mm = (
                    self.sb_looming_center_mm_x.value(),
                    self.sb_looming_center_mm_y.value()
                ),
                looming_period_sec = self.sb_looming_period_sec.value(),
                looming_expansion_time_sec = self.sb_looming_expansion_time_sec.value(),
                looming_expansion_speed_mm_per_sec = self.sb_looming_expansion_speed_mm_per_sec.value(),
                stop_condition = stop_condition
            )
        
        return protocol