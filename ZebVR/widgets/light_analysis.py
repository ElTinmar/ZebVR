from PyQt5.QtWidgets import (
    QApplication, 
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLabel, 
    QPushButton, 
    QCheckBox,
    QGroupBox
)
from PyQt5.QtCore import pyqtSignal, QObject, QThread, QTimer
from qt_widgets import LabeledDoubleSpinBox, LabeledSpinBox, LabeledSliderSpinBox, LabeledComboBox
from typing import Dict, List

from thorlabs_ccs import TLCCS

# display spectrum + total power + individual led power
# overlay reference scan 
# button to calibrate power with power meter. different LEDs / all at once

class LightAnalysisWidget(QWidget):

    def __init__(self,*args,**kwargs):

        super().__init__(*args, **kwargs)

        self.declare_components()
        self.layout_components()
    
    def declare_components(self) -> None:
        ...

    def layout_components(self) -> None:
        ...

if __name__ == '__main__':

    app = QApplication([])
    window = LightAnalysisWidget()
    window.show()
    app.exec()
