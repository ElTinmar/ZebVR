from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout,
    QPushButton,
    QGroupBox,
    QCheckBox
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict, List
from qt_widgets import LabeledSpinBox
from daq_tools import Arduino_SoftTiming, LabJackU3_SoftTiming, NI_SoftTiming, BoardInfo

class DaqWidget(QWidget):

    state_changed = pyqtSignal()

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.arduino_boards: List[BoardInfo] = []
        self.labjack_boards: List[BoardInfo] = []
        self.ni_boards: List[BoardInfo] = []

        self.create_components()
        self.layout_components()
        self.refresh_boards()

    def create_components(self):
        
        self.refresh = QPushButton('Refresh boards')
        self.refresh.clicked.connect(self.refresh_boards)

        self.arduino_group = QGroupBox("Arduino")
        self.arduino_checkboxes: List[QCheckBox] = []

        self.labjack_group = QGroupBox("Labjack")
        self.labjack_checkboxes: List[QCheckBox] = []

        self.ni_group = QGroupBox("National Instruments")
        self.ni_checkboxes: List[QCheckBox] = []

    def layout_components(self) -> None:
        
        self.arduino_layout = QVBoxLayout()
        self.arduino_group.setLayout(self.arduino_layout)

        self.labjack_layout = QVBoxLayout()
        self.labjack_group.setLayout(self.labjack_layout)

        self.ni_layout = QVBoxLayout()
        self.ni_group.setLayout(self.ni_layout)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.refresh)
        layout.addWidget(self.arduino_group)
        layout.addWidget(self.labjack_group)
        layout.addWidget(self.ni_group)
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

    def refresh_boards(self) -> None:
        
        # get hardware info 
        self.arduino_boards = Arduino_SoftTiming.list_boards()
        self.labjack_boards = LabJackU3_SoftTiming.list_boards()
        self.ni_boards = NI_SoftTiming.list_boards()

        # update widgets
        for checkbox in self.arduino_checkboxes:
            self.arduino_layout.removeWidget(checkbox)
            checkbox.deleteLater()
        self.arduino_checkboxes = []

        for checkbox in self.labjack_checkboxes:
            self.labjack_layout.removeWidget(checkbox)
            checkbox.deleteLater()
        self.labjack_checkboxes = []

        for checkbox in self.ni_checkboxes:
            self.ni_layout.removeWidget(checkbox)
            checkbox.deleteLater()
        self.ni_checkboxes = []

        for board in self.arduino_boards:
            checkbox = QCheckBox(f'{board.name} - {str(board.id)}')
            self.arduino_checkboxes.append(checkbox)
            self.arduino_layout.addWidget(checkbox)
        
        for board in self.labjack_boards:
            checkbox = QCheckBox(f'{board.name} - {str(board.id)}')
            self.labjack_checkboxes.append(checkbox)
            self.labjack_layout.addWidget(checkbox)

        for board in self.ni_boards:
            checkbox = QCheckBox(f'{board.name} - {str(board.id)}')
            self.ni_checkboxes.append(checkbox)
            self.ni_layout.addWidget(checkbox)
