
from PyQt5.QtWidgets import (
    QWidget, 
    QApplication,
    QVBoxLayout,
    QGroupBox,
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict
from pathlib import Path
from qt_widgets import LabeledEditLine

class StimOutputWidget(QWidget):

    state_changed = pyqtSignal()
    FOLDER: Path = Path('output/data')

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.filename = ''
        self.declare_components()
        self.layout_components()

    def declare_components(self) -> None:

        self.stim_output_group = QGroupBox('stimulus data')

        self.edt_filename = LabeledEditLine()
        self.edt_filename.setLabel('result file:')
        self.edt_filename.setText('stim.json')
        self.edt_filename.textChanged.connect(self.state_changed)

    def update_prefix(self, prefix: str):

        self.filename = self.FOLDER / f'stim_{prefix}.json'
        self.edt_filename.setText(str(self.filename))
        self.state_changed.emit()

    def layout_components(self) -> None:

        layout = QVBoxLayout()
        layout.addWidget(self.edt_filename)
        self.stim_output_group.setLayout(layout)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.stim_output_group)

    def get_state(self) -> Dict:

        state = {}
        state['filename'] = self.edt_filename.text()
        return state
    
    def set_state(self, state: Dict) -> None:

        setters = {
            'filename': self.edt_filename.setText
        }
        
        for key, setter in setters.items():
            if key in state:
                setter(state[key])

if __name__ == "__main__":
    
    app = QApplication([])
    window = StimOutputWidget()
    window.show()
    app.exec()
