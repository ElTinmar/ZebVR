from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QGroupBox,
    QCheckBox,
    QTableWidget,
    QHeaderView,
    QFrame,
    QTableWidgetItem
)
from PyQt5.QtCore import pyqtSignal, Qt
from typing import Dict
import numpy as np
import os
import json

from qt_widgets import LabeledDoubleSpinBox, LabeledSpinBox, FileSaveLabeledEditButton

class VRSettingsWidget(QWidget):

    state_changed = pyqtSignal()
    openloop_coords_signal = pyqtSignal()
    video_recording_signal = pyqtSignal(bool)

    DEFAULT_OPENLOOP_COORD_FILE = 'ZebVR/default/open_loop_coords.json'
    DEFAULT_TRACKING_FILE =  'ZebVR/default/tracking.json'

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        
        self.heading = [[1.0, 0.0], [0.0, 1.0]] 
        self.declare_components()
        self.layout_components()

    def declare_components(self):
        

        self.openloop_group = QGroupBox('open-loop')
        self.openloop_group.setCheckable(True)
        self.openloop_group.setChecked(False)
        self.openloop_group.toggled.connect(self.toggle_openloop)

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

        self.closedloop_group = QGroupBox('closed-loop')
        self.closedloop_group.setCheckable(True)
        self.closedloop_group.setChecked(True)
        self.closedloop_group.toggled.connect(self.toggle_closedloop)
    
        self.n_background_workers = LabeledSpinBox()
        self.n_background_workers.setText('# background subtraction workers:')
        self.n_background_workers.setValue(1)
        self.n_background_workers.valueChanged.connect(self.state_changed)

        self.background_gpu = QCheckBox('GPU background subtraction')
        self.background_gpu.setChecked(True)
        self.background_gpu.stateChanged.connect(self.state_changed)
    
        self.n_tracker_workers = LabeledSpinBox()
        self.n_tracker_workers.setText('# tracker workers:')
        self.n_tracker_workers.setValue(1)
        self.n_tracker_workers.valueChanged.connect(self.state_changed)

        self.n_tail_pts_interp = LabeledSpinBox()
        self.n_tail_pts_interp.setText('# tail points interp:')
        self.n_tail_pts_interp.setValue(40)
        self.n_tail_pts_interp.valueChanged.connect(self.state_changed)

        self.tracking_settings = FileSaveLabeledEditButton()
        self.tracking_settings.setLabel('tracker settings file:')
        self.tracking_settings.setDefault(self.DEFAULT_TRACKING_FILE)
        self.tracking_settings.textChanged.connect(self.state_changed)

        self.queue_refresh_time_microsec = LabeledSpinBox()
        self.queue_refresh_time_microsec.setText(u'queue refresh time (\N{GREEK SMALL LETTER MU}s):')
        self.queue_refresh_time_microsec.setRange(1,100_000)
        self.queue_refresh_time_microsec.setValue(100)
        self.queue_refresh_time_microsec.valueChanged.connect(self.state_changed)

        self.display_fps = LabeledSpinBox()
        self.display_fps.setText('FPS display:')
        self.display_fps.setValue(30)
        self.display_fps.valueChanged.connect(self.state_changed)
        
        #TODO when this is active toggle output widget video_group 
        self.videorecording_checkbox = QCheckBox('video recording only')
        self.videorecording_checkbox.setChecked(False)
        self.videorecording_checkbox.toggled.connect(self.toggle_videorecording)

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

        closedloop_layout = QVBoxLayout()
        closedloop_layout.addWidget(self.background_gpu)
        closedloop_layout.addWidget(self.n_background_workers)
        closedloop_layout.addWidget(self.n_tracker_workers)
        closedloop_layout.addWidget(self.n_tail_pts_interp)
        closedloop_layout.addWidget(self.display_fps)
        closedloop_layout.addWidget(self.tracking_settings)
        self.closedloop_group.setLayout(closedloop_layout)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.closedloop_group)
        main_layout.addWidget(self.openloop_group)
        main_layout.addWidget(self.videorecording_checkbox)
        main_layout.addWidget(self.queue_refresh_time_microsec)
        main_layout.addStretch()

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

    def toggle_openloop(self, isChecked: bool):
        if isChecked:
            self.closedloop_group.setChecked(False)
            self.videorecording_checkbox.setChecked(False)
        self.state_changed.emit()

    def toggle_closedloop(self, isChecked: bool):
        if isChecked:
            self.openloop_group.setChecked(False)
            self.videorecording_checkbox.setChecked(False)
        self.state_changed.emit()

    def toggle_videorecording(self, isChecked: bool):
        if isChecked:
            self.openloop_group.setChecked(False)
            self.closedloop_group.setChecked(False)
        self.state_changed.emit()
        self.video_recording_signal.emit(isChecked)

    def get_state(self) -> Dict:

        state = {}
        state['openloop'] = self.openloop_group.isChecked()
        state['closedloop'] = self.closedloop_group.isChecked()
        state['videorecording'] = self.videorecording_checkbox.isChecked()
        state['openloop_coords_file'] = self.openloop_coords_file.text()
        state['tracking_file'] = self.tracking_settings.text()
        state['centroid_x'] = self.centroid_x.value()
        state['centroid_y'] = self.centroid_y.value()
        state['heading'] = self.heading
        state['n_background_workers'] = self.n_background_workers.value()
        state['n_tracker_workers'] = self.n_tracker_workers.value()
        state['background_gpu'] = self.background_gpu.isChecked()
        state['n_tail_pts_interp'] = self.n_tail_pts_interp.value()
        state['queue_refresh_time_microsec'] = self.queue_refresh_time_microsec.value()
        state['display_fps'] = self.display_fps.value()
        return state
    
    def set_state(self, state: Dict) -> None:

        try:
            self.openloop_group.setChecked(state['openloop'])
            self.closedloop_group.setChecked(state['closedloop'])
            self.videorecording_checkbox.setChecked(state['videorecording'])
            self.openloop_coords_file.setText(state['openloop_coords_file'])
            self.tracking_settings.setText(state['tracking_file'])
            self.centroid_x.setValue(state['centroid_x'])
            self.centroid_y.setValue(state['centroid_y'])
            self.heading = state['heading']
            self.n_background_workers.setValue(state['n_background_workers'])
            self.n_tracker_workers.setValue(state['n_tracker_workers'])
            self.background_gpu.setChecked(state['background_gpu'])
            self.n_tail_pts_interp.setValue(state['n_tail_pts_interp'])
            self.queue_refresh_time_microsec.setValue(state['queue_refresh_time_microsec'])
            self.display_fps.setValue(state['display_fps'])
            self.update_table()

        except KeyError:
            print('Wrong state keys provided to VR setting widget')
            raise

if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication, QMainWindow
    from PyQt5.QtCore import  QRunnable, QThreadPool

    class Window(QMainWindow):

        def __init__(self,*args,**kwargs):

            super().__init__(*args, **kwargs)
            self.openloop_widget = VRSettingsWidget()
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
