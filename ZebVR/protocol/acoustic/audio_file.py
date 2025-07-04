from ...protocol import (
    Stim, 
    ProtocolItem, 
    AudioProtocolItem, 
    AudioProtocolItemWidget, 
    StopWidget, 
    Debouncer
)
from typing import Tuple, Dict
from qt_widgets import LabeledDoubleSpinBox, FileOpenLabeledEditButton
from PyQt5.QtWidgets import (
    QGroupBox, 
    QVBoxLayout,
    QApplication, 
)
from ...utils import set_from_dict
from ..default import DEFAULT

class AudioFile(AudioProtocolItem):

    STIM_SELECT = Stim.IMAGE

    def __init__(
            self, 
            audio_file_path: str = DEFAULT['audio_file_path'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.audio_file_path = audio_file_path

    def start(self) -> Dict:

        super().start()

        command = {
            'stim_select': self.STIM_SELECT,
            'audio_file_path': self.audio_file_path,
            'amplitude_dB': self.amplitude_dB,
        }
        return command
    
class AudioFileWidget(AudioProtocolItemWidget):

    def __init__(
            self,
            audio_file_path: str = DEFAULT['audio_file_path'],
            *args, 
            **kwargs
        ) -> None:

        self.audio_file_path = audio_file_path
        
        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.fs_audio_file_path = FileOpenLabeledEditButton()
        self.fs_audio_file_path.setText(self.audio_file_path)
        self.fs_audio_file_path.textChanged.connect(self.state_changed)


    def layout_components(self) -> None:
        
        super().layout_components()

        image_layout = QVBoxLayout()
        image_layout.addWidget(self.fs_audio_file_path)
        image_layout.addStretch()

        self.image_group = QGroupBox('Audio file')
        self.image_group.setLayout(image_layout)

        self.main_layout.addWidget(self.image_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:
        
        state = super().get_state()
        state['audio_file_path'] = self.fs_audio_file_path.text()
        return state
    
    def set_state(self, state: Dict) -> None:
        
        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'audio_file_path',
            setter = self.fs_audio_file_path.setText,
            default = self.audio_file_path,
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:

        super().from_protocol_item(protocol_item)

        if isinstance(protocol_item, AudioFile):
            self.fs_audio_file_path.setText(protocol_item.audio_file_path)

    def to_protocol_item(self) -> AudioFile:
        
        protocol = AudioFile(
            audio_file_path = self.fs_audio_file_path.text(),
            amplitude_dB = self.sb_amplitude_dB.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )
        return protocol
    
if __name__ == '__main__':

    app = QApplication([])
    window = AudioFileWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
 