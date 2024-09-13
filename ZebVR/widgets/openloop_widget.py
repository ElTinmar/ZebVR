from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout,
    QHBoxLayout,
    QPushButton
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict

from qt_widgets import LabeledDoubleSpinBox, LabeledComboBox, FileSaveLabeledEditButton

class OpenLoopWidget(QWidget):

    state_changed = pyqtSignal()
    openloop_signal = pyqtSignal()

    DEFAULT_FILE = 'ZebVR/default/open_loop_coords.json'


    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.declare_components()
        self.layout_components()
        self.method_change('closed-loop')

    def declare_components(self):
        
        # video recording
        self.vr_choice = LabeledComboBox(self)
        self.vr_choice.setText('VR type')
        self.vr_choice.addItem('closed-loop')
        self.vr_choice.addItem('open-loop')
        self.vr_choice.currentTextChanged.connect(self.method_change)

        self.openloop_coords_file = FileSaveLabeledEditButton()
        self.openloop_coords_file.setLabel('open-loop coords file:')
        self.openloop_coords_file.setDefault(self.DEFAULT_FILE)
        self.openloop_coords_file.textChanged.connect(self.state_changed)

        self.openloop_coords = QPushButton('open-loop coords')
        self.openloop_coords.clicked.connect(self.openloop_signal)

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

        self.direction_x = LabeledDoubleSpinBox()
        self.direction_x.setText('direction X:')
        self.direction_x.setRange(-1,1)
        self.direction_x.setSingleStep(0.05)
        self.direction_x.setValue(0)
        self.direction_x.valueChanged.connect(self.state_changed)

        self.direction_y = LabeledDoubleSpinBox()
        self.direction_y.setText('direction Y:')
        self.direction_y.setRange(-1,1)
        self.direction_y.setSingleStep(0.05)
        self.direction_y.setValue(1)
        self.direction_y.valueChanged.connect(self.state_changed)

    def layout_components(self):
        
        layout_centroid = QHBoxLayout()
        layout_centroid.addWidget(self.centroid_x)
        layout_centroid.addWidget(self.centroid_y)

        layout_direction = QHBoxLayout()
        layout_direction.addWidget(self.direction_x)
        layout_direction.addWidget(self.direction_y)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.vr_choice)
        main_layout.addWidget(self.openloop_coords_file)
        main_layout.addWidget(self.openloop_coords)
        main_layout.addLayout(layout_centroid)
        main_layout.addLayout(layout_direction)
        main_layout.addStretch()

    def method_change(self, vr_type: str):

        if vr_type == 'closed-loop':
            self.openloop_coords.setEnabled(False)
            self.openloop_coords_file.setEnabled(False)
            self.centroid_x.setEnabled(False)
            self.centroid_y.setEnabled(False)
            self.direction_x.setEnabled(False)
            self.direction_y.setEnabled(False)
            
        else:
            self.openloop_coords.setEnabled(True)
            self.openloop_coords_file.setEnabled(True)
            self.centroid_x.setEnabled(True)
            self.centroid_y.setEnabled(True)
            self.direction_x.setEnabled(True)
            self.direction_y.setEnabled(True)

        self.state_changed.emit()

    def get_state(self) -> Dict:

        state = {}
        state['vr_type'] = self.vr_choice.currentIndex()
        state['openloop_coords_file'] = self.openloop_coords_file.text()
        state['centroid_x'] = self.centroid_x.value()
        state['centroid_y'] = self.centroid_y.value()
        state['direction_x'] = self.direction_x.value()
        state['direction_y'] = self.direction_y.value()
        return state
    
    def set_state(self, state: Dict) -> None:

        try:
            self.vr_choice.setCurrentIndex(state['vr_type'])
            self.openloop_coords_file.setText(state['openloop_coords_file'])
            self.centroid_x.setValue(state['centroid_x'])
            self.centroid_y.setValue(state['centroid_y'])
            self.direction_x.setValue(state['direction_x'])
            self.direction_y.setValue(state['direction_y'])

        except KeyError:
            print('Wrong state keys provided to openloop widget')
            raise

if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication, QMainWindow
    from PyQt5.QtCore import  QRunnable, QThreadPool

    class Window(QMainWindow):

        def __init__(self,*args,**kwargs):

            super().__init__(*args, **kwargs)
            self.openloop_widget = OpenLoopWidget()
            self.setCentralWidget(self.openloop_widget)
            self.openloop_widget.state_changed.connect(self.state_changed)
            self.openloop_widget.openloop_signal.connect(self.openloop)

        def state_changed(self):
            print(self.openloop_widget.get_state())

        def openloop(self):
            print('openloop coords clicked')
    
    app = QApplication([])
    window = Window()
    window.show()
    app.exec()
