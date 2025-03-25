from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGroupBox,
    QTableWidget,
    QHeaderView,
    QFrame,
    QTableWidgetItem,
    QApplication
)
from PyQt5.QtCore import pyqtSignal, Qt
from typing import Dict
import os
import json

from qt_widgets import LabeledDoubleSpinBox, FileSaveLabeledEditButton

class OpenLoopWidget(QWidget):

    state_changed = pyqtSignal()
    openloop_coords_signal = pyqtSignal()

    DEFAULT_OPENLOOP_COORD_FILE = 'ZebVR/default/open_loop_coords.json'

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        
        self.heading = [[1.0, 0.0], [0.0, 1.0]] 
        self.declare_components()
        self.layout_components()

    def declare_components(self) -> None:
        
        self.openloop_group = QGroupBox('open-loop')

        self.openloop_coords_file = FileSaveLabeledEditButton()
        self.openloop_coords_file.setLabel('open-loop coords file:')
        self.openloop_coords_file.setDefault(self.DEFAULT_OPENLOOP_COORD_FILE)
        self.openloop_coords_file.textChanged.connect(self.state_changed)

        self.openloop_coords = QPushButton('open-loop coords')
        self.openloop_coords.clicked.connect(self.openloop_coords_signal)

        self.centroid_x = LabeledDoubleSpinBox()
        self.centroid_x.setText('offset X:')
        self.centroid_x.setRange(0,10_000)
        self.centroid_x.setValue(0)
        self.centroid_x.valueChanged.connect(self.state_changed)

        self.centroid_y = LabeledDoubleSpinBox()
        self.centroid_y.setText('offset Y:')
        self.centroid_y.setRange(0,10_000)
        self.centroid_y.setValue(0)
        self.centroid_y.valueChanged.connect(self.state_changed)

        self.heading_table = QTableWidget()
        self.heading_table.setRowCount(2)
        self.heading_table.setColumnCount(2)  
        self.heading_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.heading_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.heading_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.heading_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.heading_table.setHorizontalHeaderItem(0, QTableWidgetItem('PC1'))
        self.heading_table.setHorizontalHeaderItem(1, QTableWidgetItem('PC2'))
        self.heading_table.setVerticalHeaderItem(0, QTableWidgetItem('x'))
        self.heading_table.setVerticalHeaderItem(1, QTableWidgetItem('y'))
        self.heading_table.setFrameShape(QFrame.NoFrame)
        self.heading_table.setMaximumHeight(100)
        self.heading_table.setEnabled(True)
        self.heading_table.cellChanged.connect(self.table_callback)

        if os.path.exists(self.DEFAULT_OPENLOOP_COORD_FILE):
            with open(self.DEFAULT_OPENLOOP_COORD_FILE, 'r') as f:
                state = json.load(f)
                self.set_state(state)

        self.update_table()

    def layout_components(self) -> None:
        
        layout_centroid = QHBoxLayout()
        layout_centroid.addWidget(self.centroid_x)
        layout_centroid.addWidget(self.centroid_y)

        openloop_layout = QVBoxLayout()
        openloop_layout.addWidget(self.openloop_coords_file)
        openloop_layout.addWidget(self.openloop_coords)
        openloop_layout.addLayout(layout_centroid)
        openloop_layout.addWidget(self.heading_table)
        self.openloop_group.setLayout(openloop_layout)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.openloop_group)

    def update_table(self):
        for i in range(2):
            for j in range(2):
                self.heading_table.setItem(i,j,QTableWidgetItem(f'{self.heading[i][j]:2f}'))

    def table_callback(self, row, col):
        item = self.heading_table.item(row, col)
        try:
            value = float(item.text())
            self.heading[row][col] = value
        except ValueError:
            self.heading_table.setItem(row, col, QTableWidgetItem(f'{0:2f}'))
            self.heading[row][col] = 0

    def get_state(self) -> Dict:

        state = {}
        state['openloop_coords_file'] = self.openloop_coords_file.text()
        state['centroid'] = (self.centroid_x.value(), self.centroid_y.value())
        state['heading'] = self.heading
        return state
    
    def set_state(self, state: Dict) -> None:

        setters = {
            'openloop_coords_file': self.openloop_coords_file.setText,
            'centroid': lambda x : (
                self.centroid_x.setValue(x[0]),
                self.centroid_y.setValue(x[1])
            )
        }

        for key, setter in setters.items():
            if key in state:
                setter(state[key])
        
        self.heading = state.get('heading', [[1.0, 0.0], [0.0, 1.0]])
        self.update_table()

if __name__ == "__main__":

    app = QApplication([])
    window = OpenLoopWidget()
    window.show()
    app.exec()
