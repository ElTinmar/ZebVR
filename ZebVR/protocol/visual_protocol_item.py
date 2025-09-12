from .protocol_item import VisualProtocolItem, ProtocolItem, ProtocolItemWidget
from .default import DEFAULT
from typing import Tuple, Dict
from qt_widgets import LabeledDoubleSpinBox
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QLabel,
    QHBoxLayout,
)
from ..utils import set_from_dict

# TODO: calibration, display power for each channel

class VisualProtocolItemWidget(ProtocolItemWidget):
    
    state_changed = pyqtSignal()

    def __init__(
            self,
            foreground_color: Tuple = DEFAULT['foreground_color'],
            background_color: Tuple = DEFAULT['background_color'],
            *args,
            **kwargs
        ) -> None:

        self.foreground_color = foreground_color
        self.background_color = background_color

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.lbl_foreground_color = QLabel('Foreground color:')

        self.sb_foreground_color_R = LabeledDoubleSpinBox()
        self.sb_foreground_color_R.setText('R')
        self.sb_foreground_color_R.setRange(0,1)
        self.sb_foreground_color_R.setSingleStep(0.05)
        self.sb_foreground_color_R.setValue(self.foreground_color[0])
        self.sb_foreground_color_R.valueChanged.connect(self.state_changed)

        self.sb_foreground_color_G = LabeledDoubleSpinBox()
        self.sb_foreground_color_G.setText('G')
        self.sb_foreground_color_G.setRange(0,1)
        self.sb_foreground_color_G.setSingleStep(0.05)
        self.sb_foreground_color_G.setValue(self.foreground_color[1])
        self.sb_foreground_color_G.valueChanged.connect(self.state_changed)

        self.sb_foreground_color_B = LabeledDoubleSpinBox()
        self.sb_foreground_color_B.setText('B')
        self.sb_foreground_color_B.setRange(0,1)
        self.sb_foreground_color_B.setSingleStep(0.05)
        self.sb_foreground_color_B.setValue(self.foreground_color[2])
        self.sb_foreground_color_B.valueChanged.connect(self.state_changed)

        self.sb_foreground_color_A = LabeledDoubleSpinBox()
        self.sb_foreground_color_A.setText('A')
        self.sb_foreground_color_A.setRange(0,1)
        self.sb_foreground_color_A.setSingleStep(0.05)
        self.sb_foreground_color_A.setValue(self.foreground_color[3])
        self.sb_foreground_color_A.valueChanged.connect(self.state_changed)

        self.lbl_background_color = QLabel('Background color:')

        self.sb_background_color_R = LabeledDoubleSpinBox()
        self.sb_background_color_R.setText('R')
        self.sb_background_color_R.setRange(0,1)
        self.sb_background_color_R.setSingleStep(0.05)
        self.sb_background_color_R.setValue(self.background_color[0])
        self.sb_background_color_R.valueChanged.connect(self.state_changed)

        self.sb_background_color_G = LabeledDoubleSpinBox()
        self.sb_background_color_G.setText('G')
        self.sb_background_color_G.setRange(0,1)
        self.sb_background_color_G.setSingleStep(0.05)
        self.sb_background_color_G.setValue(self.background_color[1])
        self.sb_background_color_G.valueChanged.connect(self.state_changed)

        self.sb_background_color_B = LabeledDoubleSpinBox()
        self.sb_background_color_B.setText('B')
        self.sb_background_color_B.setRange(0,1)
        self.sb_background_color_B.setSingleStep(0.05)
        self.sb_background_color_B.setValue(self.background_color[2])
        self.sb_background_color_B.valueChanged.connect(self.state_changed)

        self.sb_background_color_A = LabeledDoubleSpinBox()
        self.sb_background_color_A.setText('A')
        self.sb_background_color_A.setRange(0,1)
        self.sb_background_color_A.setSingleStep(0.05)
        self.sb_background_color_A.setValue(self.background_color[3])
        self.sb_background_color_A.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:

        super().layout_components()

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

        self.main_layout.addLayout(foreground_color_layout)
        self.main_layout.addLayout(background_color_layout)

    def get_state(self) -> Dict:

        state = super().get_state()

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

    def set_state(self, state: Dict) -> None:

        super().set_state(state)
        
        set_from_dict(
            dictionary = state,
            key = 'foreground_color',
            setter = self.sb_foreground_color_R.setValue,
            default = self.foreground_color,
            cast = lambda x: float(x[0])
        )
        set_from_dict(
            dictionary = state,
            key = 'foreground_color',
            setter = self.sb_foreground_color_G.setValue,
            default = self.foreground_color,
            cast = lambda x: float(x[1])
        )
        set_from_dict(
            dictionary = state,
            key = 'foreground_color',
            setter = self.sb_foreground_color_B.setValue,
            default = self.foreground_color,
            cast = lambda x: float(x[2])
        )
        set_from_dict(
            dictionary = state,
            key = 'foreground_color',
            setter = self.sb_foreground_color_A.setValue,
            default = self.foreground_color,
            cast = lambda x: float(x[3])
        )

        set_from_dict(
            dictionary = state,
            key = 'background_color',
            setter = self.sb_background_color_R.setValue,
            default = self.background_color,
            cast = lambda x: float(x[0])
        )
        set_from_dict(
            dictionary = state,
            key = 'background_color',
            setter = self.sb_background_color_G.setValue,
            default = self.background_color,
            cast = lambda x: float(x[1])
        )
        set_from_dict(
            dictionary = state,
            key = 'background_color',
            setter = self.sb_background_color_B.setValue,
            default = self.background_color,
            cast = lambda x: float(x[2])
        )
        set_from_dict(
            dictionary = state,
            key = 'background_color',
            setter = self.sb_background_color_A.setValue,
            default = self.background_color,
            cast = lambda x: float(x[3])
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:
        
        super().from_protocol_item(protocol_item)

        if isinstance(protocol_item, VisualProtocolItem):
            self.sb_foreground_color_R.setValue(protocol_item.foreground_color[0])
            self.sb_foreground_color_G.setValue(protocol_item.foreground_color[1])
            self.sb_foreground_color_B.setValue(protocol_item.foreground_color[2])
            self.sb_foreground_color_A.setValue(protocol_item.foreground_color[3])
            
            self.sb_background_color_R.setValue(protocol_item.background_color[0])
            self.sb_background_color_G.setValue(protocol_item.background_color[1])
            self.sb_background_color_B.setValue(protocol_item.background_color[2])
            self.sb_background_color_A.setValue(protocol_item.background_color[3])  

    def to_protocol_item(self) -> VisualProtocolItem:
        ...

