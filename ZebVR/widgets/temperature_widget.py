from PyQt5.QtWidgets import (
    QApplication,
    QWidget, 
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout
)
from PyQt5.QtCore import pyqtSignal, QObject, QRunnable, QThreadPool, QTimer


from ..serial_utils import list_serial_arduino

class TemperatureWidget(QWidget):

    def __init__(self,*args,**kwargs):
        super().__init__(*args, **kwargs)
        self.current_temperature: float = 0

class TemperatureMonitor(QRunnable):
    pass

class TemperatureController(QObject):
    pass

if __name__ == "__main__":

    app = QApplication([])
    window = TemperatureWidget()
    window.show()
    app.exec()
