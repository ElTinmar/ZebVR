from ...protocol import (
    Stim, 
    ProtocolItem, 
    VisualProtocolItem,
    VisualProtocolItemWidget, 
    StopWidget, 
    Debouncer
)
from typing import Any, Dict
from qt_widgets import LabeledDoubleSpinBox
from qtpy.QtWidgets import (
    QGroupBox, 
    QVBoxLayout,
    QApplication, 
)
from ...utils import set_from_dict
from ..default import DEFAULT

class OKR(VisualProtocolItem):

    STIM_SELECT = Stim.OKR

    def __init__(
            self, 
            okr_spatial_frequency_deg: float = DEFAULT['okr_spatial_frequency_deg'],
            okr_speed_deg_per_sec: float = DEFAULT['okr_speed_deg_per_sec'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.okr_spatial_frequency_deg = okr_spatial_frequency_deg
        self.okr_speed_deg_per_sec = okr_speed_deg_per_sec

    def start(self) -> Dict:

        command = super().start()
        command.update({
            'stim_select': self.STIM_SELECT,
            'okr_spatial_frequency_deg': self.okr_spatial_frequency_deg,
            'okr_speed_deg_per_sec': self.okr_speed_deg_per_sec
        })
        return command
    
class OKR_Widget(VisualProtocolItemWidget):

    def __init__(
            self,
            okr_spatial_frequency_deg: float = DEFAULT['okr_spatial_frequency_deg'],
            okr_speed_deg_per_sec: float = DEFAULT['okr_speed_deg_per_sec'],
            *args, 
            **kwargs
        ) -> None:

        self.okr_spatial_frequency_deg = okr_spatial_frequency_deg
        self.okr_speed_deg_per_sec = okr_speed_deg_per_sec
        
        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.sb_okr_spatial_freq = LabeledDoubleSpinBox()
        self.sb_okr_spatial_freq.setText('Spatial frequence (deg)')
        self.sb_okr_spatial_freq.setRange(0,10_000)
        self.sb_okr_spatial_freq.setValue(self.okr_spatial_frequency_deg)
        self.sb_okr_spatial_freq.valueChanged.connect(self.state_changed)

        self.sb_okr_speed = LabeledDoubleSpinBox()
        self.sb_okr_speed.setText('speed (deg/s)')
        self.sb_okr_speed.setRange(-10_000,10_000)
        self.sb_okr_speed.setValue(self.okr_speed_deg_per_sec)
        self.sb_okr_speed.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:
        
        super().layout_components()

        okr_layout = QVBoxLayout()
        okr_layout.addWidget(self.sb_okr_spatial_freq)
        okr_layout.addWidget(self.sb_okr_speed)
        okr_layout.addStretch()

        self.okr_group = QGroupBox('OKR parameters')
        self.okr_group.setLayout(okr_layout)

        self.main_layout.addWidget(self.okr_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:
        
        state = super().get_state()
        state['okr_spatial_frequency_deg'] = self.sb_okr_spatial_freq.value()
        state['okr_speed_deg_per_sec'] = self.sb_okr_speed.value()
        return state
    
    def set_state(self, state: Dict) -> None:
        
        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'okr_spatial_frequency_deg',
            setter = self.sb_okr_spatial_freq.setValue,
            default = self.okr_spatial_frequency_deg,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'okr_speed_deg_per_sec',
            setter = self.sb_okr_speed.setValue,
            default = self.okr_speed_deg_per_sec,
            cast = float
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:

        super().from_protocol_item(protocol_item)

        if isinstance(protocol_item, OKR):
            self.sb_okr_spatial_freq.setValue(protocol_item.okr_spatial_frequency_deg)
            self.sb_okr_speed.setValue(protocol_item.okr_speed_deg_per_sec)

    def _get_protocol_kwargs(self) -> Dict[str, Any]:

        kwargs = super()._get_protocol_kwargs()
        
        kwargs.update({
            'okr_spatial_frequency_deg': self.sb_okr_spatial_freq.value(),
            'okr_speed_deg_per_sec': self.sb_okr_speed.value(),
        })
        return kwargs
    
    def to_protocol_item(self) -> OKR:
        return OKR(**self._get_protocol_kwargs())
    
if __name__ == '__main__':

    app = QApplication([])
    window = OKR_Widget(
        okr_spatial_frequency_deg = 20,
        okr_speed_deg_per_sec = 36,
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
 
