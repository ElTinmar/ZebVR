from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGroupBox,
    QTableWidget,
    QHeaderView,
    QFrame,
    QTableWidgetItem
)
from PyQt5.QtCore import pyqtSignal, Qt
from typing import Dict
import os
import json

from qt_widgets import LabeledDoubleSpinBox, FileSaveLabeledEditButton

class OpenLoopWidget(QWidget):

    state_changed = pyqtSignal()
    openloop_coords_signal = pyqtSignal()
    video_recording_signal = pyqtSignal(bool)

    DEFAULT_OPENLOOP_COORD_FILE = 'ZebVR/default/open_loop_coords.json'

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        
        self.heading = [[1.0, 0.0], [0.0, 1.0]] 
        self.declare_components()
        self.layout_components()

    def declare_components(self):
        
        self.openloop_group = QGroupBox('open-loop')

        self.openloop_coords_file = FileSaveLabeledEditButton()
        self.openloop_coords_file.setLabel('open-loop coords file:')
        self.openloop_coords_file.setDefault(self.DEFAULT_OPENLOOP_COORD_FILE)
        self.openloop_coords_file.textChanged.connect(self.state_changed)

        self.openloop_coords = QPushButton('open-loop coords')
        self.openloop_coords.clicked.connect(self.openloop_coords_signal)

        self.centroid_x = LabeledDoubleSpinBox()
        self.centroid_x.setText('centroid X:')
        self.centroid_x.setRange(0,10_000)
        self.centroid_x.setValue(0)
        self.centroid_x.valueChanged.connect(self.state_changed)

        self.centroid_y = LabeledDoubleSpinBox()
        self.centroid_y.setText('centroid Y:')
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
                data = json.load(f)
            self.heading = data['heading']
            self.centroid_x.setValue(data['centroid'][0])
            self.centroid_y.setValue(data['centroid'][1])

        self.update_table()

    def layout_components(self):
        
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
        state['centroid_x'] = self.centroid_x.value()
        state['centroid_y'] = self.centroid_y.value()
        state['heading'] = self.heading
        return state
    
    def set_state(self, state: Dict) -> None:

        try:
            self.openloop_coords_file.setText(state['openloop_coords_file'])
            self.centroid_x.setValue(state['centroid_x'])
            self.centroid_y.setValue(state['centroid_y'])
            self.heading = state['heading']
            self.update_table()

        except KeyError:
            print('Wrong state keys provided to VR setting widget')
            raise

if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication, QMainWindow

    class Window(QMainWindow):

        def __init__(self,*args,**kwargs):

            super().__init__(*args, **kwargs)
            self.openloop_widget = OpenLoopWidget()
            self.setCentralWidget(self.openloop_widget)
            self.openloop_widget.state_changed.connect(self.state_changed)
            self.openloop_widget.openloop_coords_signal.connect(self.openloop)

        def state_changed(self):
            print(self.openloop_widget.get_state())

        def openloop(self):
            print('openloop coords clicked')
    
    app = QApplication([])
    window = Window()
    window.show()
    app.exec()
