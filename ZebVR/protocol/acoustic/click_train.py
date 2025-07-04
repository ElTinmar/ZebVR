from ZebVR.protocol import (
    Stim, 
    ProtocolItem, 
    AudioProtocolItem,
    AudioProtocolItemWidget, 
    StopWidget, 
    Debouncer
)
from typing import Dict
from PyQt5.QtWidgets import (
    QApplication, 
    QVBoxLayout,
    QGroupBox
)
from qt_widgets import LabeledDoubleSpinBox, LabeledComboBox
from ..default import DEFAULT
from ...utils import set_from_dict
from enum import IntEnum

class ClickPolarity(IntEnum):
    BIPHASIC = 0
    POSITIVE = 1

    def __str__(self) -> str:
        return self.name

class ClickTrain(AudioProtocolItem):

    STIM_SELECT = Stim.CLICK_TRAIN

    def __init__(
            self, 
            click_rate: float = DEFAULT['click_rate'],
            click_duration: float = DEFAULT['click_duration'],
            click_polarity: ClickPolarity = DEFAULT['click_polarity'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.click_rate = click_rate
        self.click_duration = click_duration
        self.click_polarity = click_polarity

    def start(self) -> Dict:

        super().start()
        
        command = {
            'stim_select': self.STIM_SELECT,
            'click_rate': self.click_rate,
            'click_duration': self.click_duration,
            'click_polarity': self.click_polarity,
            'amplitude_dB': self.amplitude_dB,
        }
        return command
    
class ClickTrainWidget(AudioProtocolItemWidget):

    def __init__(
            self,
            click_rate: float = DEFAULT['click_rate'],
            click_duration: float = DEFAULT['click_duration'],
            click_polarity: ClickPolarity = DEFAULT['click_polarity'],
            *args, 
            **kwargs
        ) -> None:

        self.click_rate = click_rate
        self.click_duration = click_duration
        self.click_polarity = click_polarity

        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:
        
        super().declare_components()

        self.sb_click_rate = LabeledDoubleSpinBox()
        self.sb_click_rate.setText('Click rate (Hz)')
        self.sb_click_rate.setRange(0.1, 100.0)
        self.sb_click_rate.setValue(self.click_rate)
        self.sb_click_rate.valueChanged.connect(self.state_changed)

        self.sb_click_duration = LabeledDoubleSpinBox()
        self.sb_click_duration.setText('Click duration (s)')
        self.sb_click_duration.setRange(0.0001, 1)
        self.sb_click_duration.setValue(self.click_duration)
        self.sb_click_duration.valueChanged.connect(self.state_changed)

        self.cb_click_polarity = LabeledComboBox()
        self.cb_click_polarity.setText('Polarity')
        for click_polarity in ClickPolarity:
            self.cb_click_polarity.addItem(str(click_polarity))
        self.cb_click_polarity.setCurrentIndex(self.click_polarity)
        self.cb_click_polarity.currentIndexChanged.connect(self.state_changed)
        
    def layout_components(self) -> None:
        
        super().layout_components()

        click_layout = QVBoxLayout()
        click_layout.addWidget(self.sb_click_rate)
        click_layout.addWidget(self.sb_click_duration)
        click_layout.addWidget(self.cb_click_polarity)
        click_layout.addStretch()

        self.click_group = QGroupBox('Click parameters')
        self.click_group.setLayout(click_layout)

        self.main_layout.addWidget(self.click_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:

        state = super().get_state()
        state['click_rate'] = self.sb_click_rate.value()
        state['click_duration'] = self.sb_click_duration.value()    
        state['click_polarity'] = self.cb_click_polarity.currentIndex()
        return state
    
    def set_state(self, state: Dict) -> None:
        
        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'click_rate',
            setter = self.sb_click_rate.setValue,
            default = self.click_rate,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'click_duration',
            setter = self.sb_click_duration.setValue,
            default = self.click_duration,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'click_polarity',
            setter = self.cb_click_polarity.setCurrentIndex,
            default = self.click_polarity
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:
        
        super().from_protocol_item(protocol_item)

        if isinstance(protocol_item, ClickTrain):
            self.sb_click_rate.setValue(protocol_item.click_rate)
            self.sb_click_duration.setValue(protocol_item.click_duration)
            self.cb_click_polarity.setCurrentIndex(protocol_item.click_polarity)
        
    def to_protocol_item(self) -> ClickTrain:

        protocol = ClickTrain(
            click_rate = self.sb_click_rate.value(),
            amplitude_dB = self.sb_amplitude_dB.value(),
            click_duration = self.sb_click_duration.value(),
            click_polarity = ClickPolarity(self.cb_click_polarity.currentIndex()),
            stop_condition = self.stop_widget.to_stop_condition()
        )
        return protocol
    
if __name__ == '__main__':

    app = QApplication([])
    window = ClickTrainWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
    