from typing import Dict, Tuple
from qt_widgets import LabeledDoubleSpinBox
from collections import deque

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

# TODO should that really be in workers?
from ZebVR.workers import (
    ProtocolItemDark,
    ProtocolItemBright,
    ProtocolItemOKR,
    ProtocolItemOMR,
    ProtocolItemPhototaxis,
    ProtocolItemPause
)

from .stimulus_widget import StimWidget

class SequencerWidget(QWidget):

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
        self.stim_widget = StimWidget(
            phototaxis_polarity,
            omr_spatial_period_mm,
            omr_angle_deg,
            omr_speed_mm_per_sec,
            okr_spatial_frequency_deg,
            okr_speed_deg_per_sec,
            looming_center_mm,
            looming_period_sec,
            looming_expansion_time_sec,
            looming_expansion_speed_mm_per_sec,
            foreground_color,
            background_color
        )

        self.declare_components()
        self.layout_components()
        self.setWindowTitle('Sequencer')

    def declare_components(self) -> None:
        # pause item
        # stim items
        # scrollable list 
        # add and remove buttons
        pass

    def layout_components(self) -> None:
        pass

    def get_state(self):
        # return ProtocolItem deque to use with Protocol Worker  
        pass