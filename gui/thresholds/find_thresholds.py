from PyQt5 import QtCore, QtWidgets, QtGui
from core.abstractclasses import Camera, Background

# you need camera, background
# do background subtraction and thresholding + bwareafilter and show resulting masks
# controls:
#   - intensity threshold as well as size thresholds for bwareafilter
# display:
# current area in pixel of blobs ?

class ThresholdGUI(QtWidgets.QMainWindow):
    def __init__(
            self, 
            camera: Camera, 
            background: Background, 
            *args, 
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.camera = camera
        self.background = background
        
        self.setWindowTitle("ThresholdGUI")
        self.update_interval = 30
        self.update_timer = QtCore.QTimer()
        self.update_timer.setInterval(self.update_interval)
        self.update_timer.timeout.connect(self.update_plots)
        self.update_timer.start()
        
    @QtCore.pyqtSlot()
    def update_plots(self):
        """do somethig here"""