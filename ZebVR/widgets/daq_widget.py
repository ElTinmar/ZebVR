from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout,
    QPushButton,
    QGroupBox,
    QCheckBox,
    QLayout,
    QApplication
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict, List
from daq_tools import (
    Arduino_SoftTiming, 
    LabJackU3_SoftTiming, 
    NI_SoftTiming, 
    BoardInfo
)

class DaqWidget(QWidget):

    state_changed = pyqtSignal()

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        self.arduino_boards: List[BoardInfo] = []
        self.arduino_checkboxes: List[QCheckBox] = []
        self.labjack_boards: List[BoardInfo] = []
        self.labjack_checkboxes: List[QCheckBox] = []
        self.ni_boards: List[BoardInfo] = []
        self.ni_checkboxes: List[QCheckBox] = []

        self.create_components()
        self.layout_components()
        self.refresh_boards()

    def create_components(self):
        
        self.refresh = QPushButton('Refresh boards')
        self.refresh.clicked.connect(self.refresh_boards)

        self.arduino_group = QGroupBox("Arduino")
        self.labjack_group = QGroupBox("Labjack")
        self.ni_group = QGroupBox("National Instruments")
        
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
        
        state['arduino'] = []
        for checkbox, board in zip(self.arduino_checkboxes, self.arduino_boards):
            if checkbox.isChecked():
                state['arduino'].append(board.id)
        
        state['labjack'] = []
        for checkbox, board in zip(self.labjack_checkboxes, self.labjack_boards):
            if checkbox.isChecked():
                state['labjack'].append(board.id)

        state['ni'] = []
        for checkbox, board in zip(self.ni_checkboxes, self.ni_boards):
            if checkbox.isChecked():
                state['ni'].append(board.id)

        return state
    
    def set_state(self, state: Dict) -> None:

        setters = {}

        for key, setter in setters.items():
            if key in state:
                setter(state[key])

    def _refresh(
            self, 
            boards: List[BoardInfo], 
            checkboxes: List[QCheckBox], 
            layout: QLayout
        ) -> None:
        """relies on side-effect"""
        
        for checkbox in checkboxes:
            layout.removeWidget(checkbox)
            checkbox.deleteLater()
        checkboxes.clear()

        for board in boards:
            checkbox = QCheckBox(f'{board.name} - {str(board.id)}')
            checkbox.stateChanged.connect(self.state_changed.emit)
            checkboxes.append(checkbox)
            layout.addWidget(checkbox)

    def refresh_boards(self) -> None:
        
        # get hardware info 
        self.arduino_boards = Arduino_SoftTiming.list_boards()
        self.labjack_boards = LabJackU3_SoftTiming.list_boards()
        self.ni_boards = NI_SoftTiming.list_boards()

        self._refresh(self.arduino_boards, self.arduino_checkboxes, self.arduino_layout)
        self._refresh(self.labjack_boards, self.labjack_checkboxes, self.labjack_layout)
        self._refresh(self.ni_boards, self.ni_checkboxes, self.ni_layout)

if __name__ == "__main__":

    app = QApplication([])
    widget = DaqWidget()
    widget.show()
    app.exec_()

    print(widget.get_state())
