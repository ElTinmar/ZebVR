from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout,
    QGroupBox,
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict

from qt_widgets import LabeledEditLine

class LogOutputWidget(QWidget):

    state_changed = pyqtSignal()

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        
        self.filename = ''
        self.declare_components()
        self.layout_components()

    def declare_components(self):
        
        self.log_group = QGroupBox('Logs')

        self.worker_logfile = LabeledEditLine()
        self.worker_logfile.setLabel('worker log file:')
        self.worker_logfile.setText('workers.log')
        self.worker_logfile.textChanged.connect(self.state_changed)

        self.queue_logfile = LabeledEditLine()
        self.queue_logfile.setLabel('queue log file:')
        self.queue_logfile.setText('queues.log')
        self.queue_logfile.textChanged.connect(self.state_changed)

    def layout_components(self):

        log_layout = QVBoxLayout()
        log_layout.addWidget(self.worker_logfile)
        log_layout.addWidget(self.queue_logfile)
        self.log_group.setLayout(log_layout)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.log_group)
        main_layout.addStretch()

    def get_state(self) -> Dict:
        state = {}
        state['worker_logfile'] = self.worker_logfile.text()
        state['queue_logfile'] = self.queue_logfile.text()
        return state
    
    def set_state(self, state: Dict) -> None:
        try:
            self.worker_logfile.setText(state['worker_logfile'])
            self.queue_logfile.setText(state['queue_logfile'])

        except KeyError:
            print('Wrong state keys provided to output widget')
            raise

if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication, QMainWindow

    class Window(QMainWindow):

        def __init__(self,*args,**kwargs):

            super().__init__(*args, **kwargs)
            self.output_widget = LogOutputWidget()
            self.setCentralWidget(self.output_widget)
            self.output_widget.state_changed.connect(self.state_changed)

        def state_changed(self):
            print(self.output_widget.get_state())
    
    app = QApplication([])
    window = Window()
    window.show()
    app.exec()
