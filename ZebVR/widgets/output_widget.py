from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict

from qt_widgets import LabeledSpinBox, LabeledEditLine

class OutputWidget(QWidget):

    state_changed = pyqtSignal()

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        
        self.filename = ''
        self.declare_components()
        self.layout_components()

    def declare_components(self):
        
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
        self.edt_filename.setText(f'{self.fish_id.value():02}_{self.dpf.value():02}dpf.csv')
        self.edt_filename.setEnabled(False)

        self.worker_logfile = LabeledEditLine()
        self.worker_logfile.setLabel('worker log file:')
        self.worker_logfile.setText('workers.log')
        self.worker_logfile.textChanged.connect(self.state_changed)

        self.queue_logfile = LabeledEditLine()
        self.queue_logfile.setLabel('queue log file:')
        self.queue_logfile.setText('queues.log')
        self.queue_logfile.textChanged.connect(self.state_changed)
        
        # TODO add video recording

    def experiment_data(self):
        self.filename = f'{self.fish_id.value():02}_{self.dpf.value():02}dpf.csv'
        self.edt_filename.setText(self.filename)
        self.state_changed.emit()

    def layout_components(self):

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.fish_id)
        main_layout.addWidget(self.dpf)
        main_layout.addWidget(self.edt_filename)
        main_layout.addWidget(self.worker_logfile)
        main_layout.addWidget(self.queue_logfile)
        main_layout.addStretch()

    def get_state(self) -> Dict:
        state = {}
        state['fish_id'] = self.fish_id.value()
        state['dpf'] = self.dpf.value()
        state['edt_filename'] = self.edt_filename.text()
        state['worker_logfile'] = self.worker_logfile.text()
        state['queue_logfile'] = self.queue_logfile.text()
        return state
    
    def set_state(self, state: Dict) -> None:
        try:
            self.fish_id.setValue(state['fish_id'])
            self.fish_id.setValue(state['dpf'])
            self.edt_filename.setText(state['edt_filename'])
            self.worker_logfile.setText(state['worker_logfile'])
            self.queue_logfile.setText(state['queue_logfile'])

        except KeyError:
            print('Wrong state keys provided to output widget')
            raise

if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication, QMainWindow
    from PyQt5.QtCore import  QRunnable, QThreadPool

    class Window(QMainWindow):

        def __init__(self,*args,**kwargs):

            super().__init__(*args, **kwargs)
            self.output_widget = OutputWidget()
            self.setCentralWidget(self.output_widget)
            self.output_widget.state_changed.connect(self.state_changed)

        def state_changed(self):
            print(self.output_widget.get_state())
    
    app = QApplication([])
    window = Window()
    window.show()
    app.exec()
