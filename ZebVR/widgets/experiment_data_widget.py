
from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout,
    QGroupBox,
    QPlainTextEdit,
    QLabel,
    QApplication
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict
import os

from qt_widgets import LabeledSpinBox, LabeledEditLine

class ExperimentDataWidget(QWidget):

    state_changed = pyqtSignal()
    prefix_changed = pyqtSignal(str)

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.declare_components()
        self.layout_components()

    def declare_components(self) -> None:
           
        ## data recording -----------------------------------
        self.data_group = QGroupBox('experiment data')
    
        self.experiment_id = LabeledSpinBox()
        self.experiment_id.setText('Experiment ID:')
        self.experiment_id.setValue(0)
        self.experiment_id.valueChanged.connect(self.experiment_data)

        self.dpf = LabeledSpinBox()
        self.dpf.setText('Fish age (dpf):')
        self.dpf.setValue(7)
        self.dpf.valueChanged.connect(self.experiment_data)

        self.line = LabeledEditLine()
        self.line.setLabel('Fish line:')
        self.line.setText('WT')
        self.line.textChanged.connect(self.experiment_data)

        self.label_comment = QLabel('comments')
        self.comments = QPlainTextEdit()
        self.comments.setPlaceholderText('write a comment here...')
        self.comments.setFixedHeight(50)
        self.comments.textChanged.connect(self.state_changed)

    def layout_components(self) -> None:

        data_layout = QVBoxLayout()
        data_layout.addWidget(self.experiment_id)
        data_layout.addWidget(self.dpf)
        data_layout.addWidget(self.line)
        data_layout.addWidget(self.label_comment)
        data_layout.addWidget(self.comments)
        self.data_group.setLayout(data_layout)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.data_group)

    def experiment_data(self):
        prefix = f'{self.experiment_id.value():02}_{self.dpf.value():02}dpf_{self.line.text()}'
        self.prefix_changed.emit(prefix)
        self.state_changed.emit()

    def get_state(self) -> Dict:

        state = {}
        state['experiment_id'] = self.experiment_id.value()
        state['dpf'] = self.dpf.value()
        state['line'] = self.line.text()
        state['comments'] = self.comments.toPlainText()
        return state
    
    def set_state(self, state: Dict) -> None:

        setters = {
            'experiment_id': self.experiment_id.setValue,
            'dpf': self.dpf.setValue,
            'line': self.line.setText,
            'comments': self.comments.setPlainText,
        }
        
        for key, setter in setters.items():
            if key in state:
                setter(state[key])

if __name__ == "__main__":
    
    app = QApplication([])
    window = ExperimentDataWidget()
    window.show()
    app.exec()
