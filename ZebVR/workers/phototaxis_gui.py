from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional
from PyQt5.QtWidgets import QApplication, QWidget, QCheckBox
from config import PHOTOTAXIS_POLARITY

class PhototaxisGUI(WorkerNode):

    def initialize(self) -> None:
        super().initialize()
        self.updated = False
        self.app = QApplication([])
        self.window = QWidget()
        self.declare_components()
        self.layout_components()
        self.window.setWindowTitle('Phototaxis controls')
        self.window.show()

    def declare_components(self):
        self.polarity = QCheckBox('invert polarity', self.window)
        self.polarity.stateChanged.connect(self.on_change)
        self.polarity.setChecked(PHOTOTAXIS_POLARITY)

    def layout_components(self):
        pass

    def on_change(self):
        self.updated = True

    def process_data(self, data: None) -> NDArray:
        self.app.processEvents()

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        # send only one message when things are changed
        if self.updated:
            res = {}
            res['visual_stim_control'] = {}
            res['visual_stim_control']['polarity'] = self.polarity.isChecked()
            self.updated = False
            return res       
        else:
            return None