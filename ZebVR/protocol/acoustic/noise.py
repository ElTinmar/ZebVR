from ZebVR.protocol import Stim, AudioProtocolItem, AudioProtocolItemWidget, StopWidget, Debouncer
from typing import Dict
from PyQt5.QtWidgets import (
    QApplication, 
)
from ..default import DEFAULT

class WhiteNoise(AudioProtocolItem):

    STIM_SELECT = Stim.WHITE_NOISE

    def __init__(
            self, 
            amplitude_dB: float = DEFAULT['amplitude_dB'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.amplitude_dB = amplitude_dB

    def start(self) -> Dict:

        command = super().start()
        command.update({'stim_select': self.STIM_SELECT})
        return command


class PinkNoise(AudioProtocolItem):

    STIM_SELECT = Stim.PINK_NOISE
    
    def __init__(
            self, 
            amplitude_dB: float = DEFAULT['amplitude_dB'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.amplitude_dB = amplitude_dB

    def start(self) -> Dict:

        command = super().start()
        command.update({'stim_select': self.STIM_SELECT})
        return command

class BrownNoise(AudioProtocolItem):

    STIM_SELECT = Stim.BROWN_NOISE

    def __init__(
            self, 
            amplitude_dB: float = DEFAULT['amplitude_dB'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.amplitude_dB = amplitude_dB

    def start(self) -> Dict:
        
        command = super().start()
        command.update({'stim_select': self.STIM_SELECT})
        return command

class WhiteNoiseWidget(AudioProtocolItemWidget):

    def layout_components(self) -> None:
        
        super().layout_components()
        self.main_layout.addWidget(self.stop_widget)

    def to_protocol_item(self) -> WhiteNoise:

        return WhiteNoise(
            name = self.stim_name.text(),
            amplitude_dB = self.sb_amplitude_dB.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )

class PinkNoiseWidget(AudioProtocolItemWidget):

    def layout_components(self) -> None:
        
        super().layout_components()
        self.main_layout.addWidget(self.stop_widget)
        
    def to_protocol_item(self) -> PinkNoise:

        return PinkNoise(
            name = self.stim_name.text(),
            amplitude_dB = self.sb_amplitude_dB.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )

class BrownNoiseWidget(AudioProtocolItemWidget):

    def layout_components(self) -> None:
        
        super().layout_components()
        self.main_layout.addWidget(self.stop_widget)

    def to_protocol_item(self) -> BrownNoise:

        return BrownNoise(
            name = self.stim_name.text(),
            amplitude_dB = self.sb_amplitude_dB.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )
    
if __name__ == '__main__':

    app = QApplication([])

    window0 = WhiteNoiseWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window0.show()

    window1 = PinkNoiseWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window1.show()

    window2 = BrownNoiseWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window2.show()
    
    app.exec()
    