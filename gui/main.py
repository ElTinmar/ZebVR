from PyQt5 import QtCore, QtWidgets
from core.abstractclasses import Camera, Background

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs) -> None:

        super().__init__(*args, **kwargs)
        self.setWindowTitle("ZebVR")
        self.update_interval = 30
        self.update_timer = QtCore.QTimer()
        self.update_timer.setInterval(self.update_interval)
        self.update_timer.timeout.connect(self.update_plots)
        self.update_timer.start()
        
    @QtCore.pyqtSlot()
    def update_plots(self):
        """do somethig here"""