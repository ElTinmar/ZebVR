from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QFileDialog, QCheckBox
from PyQt5.QtCore import pyqtSignal
from typing import Dict

from qt_widgets import LabeledDoubleSpinBox, LabeledSpinBox, NDarray_to_QPixmap

class RegistrationWidget(QWidget):

    def __init__(self,*args,**kwargs):

        super().__init__(*args, **kwargs)

        self.declare_components()
        self.layout_components()
    
    def declare_components(self):
        pass
   
    def layout_components(self):
        pass

    def get_state(self) -> Dict:
        state = {}
        return state
    
    def set_state(self, state: Dict) -> None:
        pass

if __name__ == "__main__":

    from PyQt5.QtWidgets import QApplication, QMainWindow
    from PyQt5.QtCore import  QRunnable, QThreadPool

    class Window(QMainWindow):

        def __init__(self,*args,**kwargs):

            super().__init__(*args, **kwargs)
            self.registration_widget = RegistrationWidget()
            self.setCentralWidget(self.registration_widget)
    
    app = QApplication([])
    window = Window()
    window.show()
    app.exec()
