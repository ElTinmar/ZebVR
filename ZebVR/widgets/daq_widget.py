from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict
from qt_widgets import LabeledSpinBox

class DaqWidget(QWidget):

    state_changed = pyqtSignal()

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.create_components()
        self.layout_components()

    def create_components(self):
        pass
        
    def layout_components(self) -> None:
        
        layout = QVBoxLayout(self)
        layout.addStretch()

    def get_state(self) -> Dict:

        state = {}
        return state
    
    def set_state(self, state: Dict) -> None:

        setters = {
        }

        for key, setter in setters.items():
            if key in state:
                setter(state[key])

        