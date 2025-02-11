from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout,
    QGroupBox,
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict
import os

from qt_widgets import LabeledSpinBox, LabeledEditLine

class TrackingOutputWidget(QWidget):

    state_changed = pyqtSignal()
    CSV_FOLDER: str = 'output/data'

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        
        self.filename = ''
        self.declare_components()
        self.layout_components()

    def declare_components(self):
        
        ## data recording -----------------------------------
        self.data_group = QGroupBox('Data')
    
        self.fish_id = LabeledSpinBox()
        self.fish_id.setText('Fish ID:')
        self.fish_id.setValue(0)
        self.fish_id.valueChanged.connect(self.experiment_data)

        self.dpf = LabeledSpinBox()
        self.dpf.setText('Fish age (dpf):')
        self.dpf.setValue(7)
        self.dpf.valueChanged.connect(self.experiment_data)

        self.edt_filename = LabeledEditLine()
        self.edt_filename.setLabel('result file:')
        self.edt_filename.setText(os.path.join(self.CSV_FOLDER, f'{self.fish_id.value():02}_{self.dpf.value():02}dpf.csv'))
        self.edt_filename.textChanged.connect(self.state_changed)
      
    def layout_components(self):
        
        data_layout = QVBoxLayout()
        data_layout.addWidget(self.fish_id)
        data_layout.addWidget(self.dpf)
        data_layout.addWidget(self.edt_filename)
        self.data_group.setLayout(data_layout)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.data_group)
        main_layout.addStretch()


    def experiment_data(self):
        self.filename = os.path.join(self.CSV_FOLDER, f'{self.fish_id.value():02}_{self.dpf.value():02}dpf.csv')
        self.edt_filename.setText(self.filename)
        self.state_changed.emit()

    def get_state(self) -> Dict:
        state = {}
        state['fish_id'] = self.fish_id.value()
        state['dpf'] = self.dpf.value()
        state['csv_filename'] = self.edt_filename.text()
        return state
    
    def set_state(self, state: Dict) -> None:
        try:
            self.fish_id.setValue(state['fish_id'])
            self.dpf.setValue(state['dpf'])
            self.edt_filename.setText(state['csv_filename'])

        except KeyError:
            print('Wrong state keys provided to output widget')
            raise

if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication, QMainWindow

    class Window(QMainWindow):

        def __init__(self,*args,**kwargs):

            super().__init__(*args, **kwargs)
            self.output_widget = TrackingOutputWidget()
            self.setCentralWidget(self.output_widget)
            self.output_widget.state_changed.connect(self.state_changed)

        def state_changed(self):
            print(self.output_widget.get_state())
    
    app = QApplication([])
    window = Window()
    window.show()
    app.exec()
