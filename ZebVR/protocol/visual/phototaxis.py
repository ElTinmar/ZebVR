from ...protocol import Stim, ProtocolItem, VisualProtocolItemWidget, StopWidget, Debouncer
from typing import Tuple, Dict
from PyQt5.QtWidgets import (
    QGroupBox, 
    QVBoxLayout,
    QApplication, 
    QCheckBox
)
from ...utils import set_from_dict
from ..default import DEFAULT

class Phototaxis(ProtocolItem):

    STIM_SELECT = Stim.Visual.PHOTOTAXIS

    def __init__(
            self, 
            phototaxis_polarity: int = DEFAULT['phototaxis_polarity'],
            foreground_color: Tuple[float, float, float, float] = DEFAULT['foreground_color'],
            background_color: Tuple[float, float, float, float] = DEFAULT['background_color'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.phototaxis_polarity = phototaxis_polarity
        self.foreground_color = foreground_color
        self.background_color = background_color 

    def start(self) -> Dict:

        super().start()

        command = {
            'stim_select': self.STIM_SELECT,
            'phototaxis_polarity': self.phototaxis_polarity,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color
        }
        return command
    
class PhototaxisWidget(VisualProtocolItemWidget):

    def __init__(
            self,
            phototaxis_polarity: int = DEFAULT['phototaxis_polarity'],
            *args, 
            **kwargs
        ) -> None:

        self.phototaxis_polarity = phototaxis_polarity

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.chb_phototaxis_polarity = QCheckBox('invert polarity')
        self.chb_phototaxis_polarity.stateChanged.connect(self.state_changed)
        self.chb_phototaxis_polarity.setChecked(self.phototaxis_polarity==1)

    def layout_components(self) -> None:
        
        super().layout_components()

        phototaxis_layout = QVBoxLayout()
        phototaxis_layout.addWidget(self.chb_phototaxis_polarity)
        phototaxis_layout.addStretch()

        self.phototaxis_group = QGroupBox('Phototaxis parameters')
        self.phototaxis_group.setLayout(phototaxis_layout)

        self.main_layout.addWidget(self.phototaxis_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:
        
        state = super().get_state()
        state['phototaxis_polarity'] = -1+2*self.chb_phototaxis_polarity.isChecked()
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

    def from_protocol_item(self, protocol_item: Phototaxis) -> None:

        super().from_protocol_item(protocol_item)

        self.chb_phototaxis_polarity.setChecked(protocol_item.phototaxis_polarity == 1) 

    def to_protocol_item(self) -> Phototaxis:
        
        foreground_color = (
            self.sb_foreground_color_R.value(), 
            self.sb_foreground_color_G.value(),
            self.sb_foreground_color_B.value(),
            self.sb_foreground_color_A.value()
        )
        background_color = (
            self.sb_background_color_R.value(), 
            self.sb_background_color_G.value(),
            self.sb_background_color_B.value(),
            self.sb_background_color_A.value()
        )
        protocol = Phototaxis(
            foreground_color = foreground_color,
            background_color = background_color,
            phototaxis_polarity = -1+2*self.chb_phototaxis_polarity.isChecked(),
            stop_condition = self.stop_widget.to_stop_condition()
        )
        return protocol
    
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
 
