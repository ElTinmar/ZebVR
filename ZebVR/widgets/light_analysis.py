from PyQt5.QtWidgets import (
    QApplication, 
    QWidget, 
    QComboBox,
    QVBoxLayout, 
    QHBoxLayout, 
    QLabel, 
    QPushButton, 
    QCheckBox,
    QGroupBox
)
from PyQt5.QtCore import pyqtSignal, QObject, QThread, QTimer
from qt_widgets import LabeledComboBox, LabeledSliderSpinBox, LabeledComboBox
from typing import Dict, List
import pyqtgraph as pg

from thorlabs_ccs import TLCCS, list_spectrometers
from thorlabs_pmd import TLPMD, list_powermeters

# discover available devices and allow selection from combobox
# display spectrum + total power + individual led power
# overlay reference scan 
# button to calibrate power with power meter. different LEDs / all at once

pg.setConfigOption('background', (251,251,251,255))
pg.setConfigOption('foreground', 'k')
pg.setConfigOption('antialias', True)

class LightAnalysisWidget(QWidget):

    def __init__(self,*args,**kwargs):

        super().__init__(*args, **kwargs)
        self.declare_components()
        self.layout_components()
    
    def declare_components(self) -> None:

        self.refresh_button = QPushButton('Refresh Devices')
        self.refresh_button.clicked.connect(self.refresh_devices)

        self.spectrometers_cb = LabeledComboBox()
        self.spectrometers_cb.setText('Spectrometer')
        
        self.powermeters_cb = LabeledComboBox()
        self.powermeters_cb.setText('Powermeter')

        self.spectrum_plot = pg.plot()
        self.spectrum_plot.setLabel('left', 'Intensity (AU)')
        self.spectrum_plot.setLabel('bottom', 'Wavelength (nm)') 

        self.total_power = QLabel('Total power: (W.cm-2)')
        self.blue_power = QLabel('Blue power: (W.cm-2)')
        self.green_power = QLabel('Green power: (W.cm-2)')
        self.red_power = QLabel('Red power: (W.cm-2)')

    def layout_components(self) -> None:

        layout = QVBoxLayout(self)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.spectrometers_cb)
        layout.addWidget(self.powermeters_cb)
        layout.addWidget(self.spectrum_plot)
        layout.addWidget(self.total_power)
        layout.addWidget(self.blue_power)
        layout.addWidget(self.green_power)
        layout.addWidget(self.red_power)
        layout.addStretch()
    
    def refresh_devices(self) -> None:

        self.spectrometers = list_spectrometers()
        self.spectrometers_cb.clear()
        for dev_info in self.spectrometers:
            self.spectrometers_cb.addItem(dev_info.serial_number)
        
        self.powermeters = list_powermeters()
        for dev_info in self.powermeters:
            self.powermeters_cb.addItem(dev_info.serial_number)

    def get_state(self) -> Dict:
        ...

    def set_state(self, state: Dict):
        ...

if __name__ == '__main__':

    app = QApplication([])
    window = LightAnalysisWidget()
    window.show()
    app.exec()
