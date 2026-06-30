from ...protocol import (
    Stim, 
    ProtocolItem, 
    VisualProtocolItem,
    VisualProtocolItemWidget, 
    StopWidget, 
    Debouncer
)
from typing import Dict, Any
from qt_widgets import LabeledDoubleSpinBox
from qtpy.QtWidgets import (
    QGroupBox, 
    QVBoxLayout,
    QApplication, 
    QCheckBox
)
from ...utils import set_from_dict
from ..default import DEFAULT

class Phototaxis(VisualProtocolItem):

    STIM_SELECT = Stim.PHOTOTAXIS

    def __init__(
            self, 
            phototaxis_polarity: int = DEFAULT['phototaxis_polarity'],
            phototaxis_transition_width_mm: float = DEFAULT['phototaxis_transition_width_mm'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.phototaxis_polarity = phototaxis_polarity
        self.phototaxis_transition_width_mm = phototaxis_transition_width_mm

    def start(self) -> Dict:

        command = super().start()
        command.update({
            'stim_select': self.STIM_SELECT,
            'phototaxis_polarity': self.phototaxis_polarity,
            'phototaxis_transition_width_mm': self.phototaxis_transition_width_mm
        })
        return command
    
class PhototaxisWidget(VisualProtocolItemWidget):

    def __init__(
            self,
            phototaxis_polarity: int = DEFAULT['phototaxis_polarity'],
            phototaxis_transition_width_mm: float = DEFAULT['phototaxis_transition_width_mm'],
            *args, 
            **kwargs
        ) -> None:

        self.phototaxis_polarity = phototaxis_polarity
        self.phototaxis_transition_width_mm = phototaxis_transition_width_mm

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.chb_phototaxis_polarity = QCheckBox('invert polarity')
        self.chb_phototaxis_polarity.stateChanged.connect(self.state_changed)
        self.chb_phototaxis_polarity.setChecked(self.phototaxis_polarity==1)

        self.sb_phototaxis_transition_width_mm = LabeledDoubleSpinBox()
        self.sb_phototaxis_transition_width_mm.setText('transition width (mm)')
        self.sb_phototaxis_transition_width_mm.setRange(0,1000)
        self.sb_phototaxis_transition_width_mm.setValue(self.phototaxis_transition_width_mm)
        self.sb_phototaxis_transition_width_mm.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:
        
        super().layout_components()

        phototaxis_layout = QVBoxLayout()
        phototaxis_layout.addWidget(self.chb_phototaxis_polarity)
        phototaxis_layout.addWidget(self.sb_phototaxis_transition_width_mm)
        phototaxis_layout.addStretch()

        self.phototaxis_group = QGroupBox('Phototaxis parameters')
        self.phototaxis_group.setLayout(phototaxis_layout)

        self.main_layout.addWidget(self.phototaxis_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:
        
        state = super().get_state()
        state['phototaxis_polarity'] = -1+2*self.chb_phototaxis_polarity.isChecked()
        state['phototaxis_transition_width_mm'] = self.sb_phototaxis_transition_width_mm.value()
        return state
    
    def set_state(self, state: Dict) -> None:
        
        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'phototaxis_polarity',
            setter = self.chb_phototaxis_polarity.setChecked,
            default = self.phototaxis_polarity == 1,
            cast = lambda x: bool((x+1)/2)
        )
        set_from_dict(
            dictionary = state,
            key = 'phototaxis_transition_width_mm',
            setter = self.sb_phototaxis_transition_width_mm.setValue,
            default = self.phototaxis_transition_width_mm,
            cast = float
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:

        super().from_protocol_item(protocol_item)

        if isinstance(protocol_item, Phototaxis):
            self.chb_phototaxis_polarity.setChecked(protocol_item.phototaxis_polarity == 1) 
    
    def _get_protocol_kwargs(self) -> Dict[str, Any]:

        kwargs = super()._get_protocol_kwargs()
        
        kwargs.update({
            'phototaxis_polarity': -1+2*self.chb_phototaxis_polarity.isChecked(),
            'phototaxis_transition_width_mm': self.sb_phototaxis_transition_width_mm.value(),
        })
        return kwargs
    
    def to_protocol_item(self) -> Phototaxis:
        return Phototaxis(**self._get_protocol_kwargs())
    
if __name__ == '__main__':

    app = QApplication([])
    window = PhototaxisWidget(
        phototaxis_polarity = 1,
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
 
