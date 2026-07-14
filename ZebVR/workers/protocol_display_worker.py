from dagline import WorkerNode
from qtpy.QtWidgets import QApplication
from ..widgets import ProtocolDisplay
import time
from ..protocol import Stim

class ProtocolDisplayWorker(WorkerNode):

    def __init__(
            self, 
            recording_duration: float = 100,
            *args, 
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.recording_duration = recording_duration

    def initialize(self):

        super().initialize()

        self.app = QApplication([])
        self.window = ProtocolDisplay(recording_duration=self.recording_duration)
        self.window.show()
        
    def process_data(self, data):
        
        self.app.processEvents()
        self.app.sendPostedEvents()
        time.sleep(0.1)
        
    def process_metadata(self, metadata: dict|None) -> None:

        if metadata is None or metadata['protocol_display'] is None:
            return
        
        stim_select = metadata['protocol_display']['stim_select']
        metadata['protocol_display']['stim_select'] = Stim(stim_select)
        self.window.set_stim_data(metadata['protocol_display'])
        
        