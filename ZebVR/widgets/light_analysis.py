from PyQt5.QtWidgets import (
    QApplication, 
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLabel, 
    QPushButton, 
    QCheckBox,
    QButtonGroup
)
from PyQt5.QtCore import pyqtSignal, QObject, QThread, QTimer
from qt_widgets import LabeledComboBox, LabeledComboBox, LabeledDoubleSpinBox
from typing import Dict
import pyqtgraph as pg

import thorlabs_ccs 
import thorlabs_pmd

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

        # Spectrometer ----

        self.spectrometers_cb = LabeledComboBox()
        self.spectrometers_cb.setText('Spectrometer')
        
        self.powermeters_cb = LabeledComboBox()
        self.powermeters_cb.setText('Powermeter')

        self.integration_time = LabeledDoubleSpinBox()
        self.integration_time.setText('Integration time (ms)')
        self.integration_time.setMinimum(thorlabs_ccs.TLCCS_MIN_INT_TIME*1000)
        self.integration_time.setMaximum(thorlabs_ccs.TLCCS_MAX_INT_TIME*1000)
        self.integration_time.setValue(thorlabs_ccs.TLCCS_DEF_INT_TIME*1000)
        self.integration_time.setSingleStep(0.01)

        self.no_correction = QCheckBox('No correction')
        self.no_correction.stateChanged.connect(self.correct_spectrum)
        self.no_correction.setChecked(True)

        self.correct_range = QCheckBox('Correct range')
        self.correct_range.stateChanged.connect(self.correct_spectrum)
        self.correct_range.setChecked(False)

        self.correct_noise = QCheckBox('Correct noise')
        self.correct_noise.stateChanged.connect(self.correct_spectrum)
        self.correct_noise.setChecked(False)

        self.correction_group = QButtonGroup()
        self.correction_group.setExclusive(True)
        self.correction_group.addButton(self.no_correction)
        self.correction_group.addButton(self.correct_range)
        self.correction_group.addButton(self.correct_noise)

        self.noise_level = LabeledDoubleSpinBox()
        self.noise_level.setText('noise amp. (dB)')
        self.noise_level.setMinimum(0)
        self.noise_level.setMaximum(30)
        self.noise_level.setValue(1.0)
        self.noise_level.setSingleStep(0.1)
        self.noise_level.setEnabled(False)

        self.wavelength_left = LabeledDoubleSpinBox()
        self.wavelength_left.setText('λ left (nm)')
        self.wavelength_left.setMinimum(0)
        self.wavelength_left.setMaximum(1000)
        self.wavelength_left.setValue(500)
        self.wavelength_left.setSingleStep(0.1)
        self.wavelength_left.setEnabled(False)

        self.wavelength_center = LabeledDoubleSpinBox()
        self.wavelength_center.setText('λ center (nm)')
        self.wavelength_center.setMinimum(0)
        self.wavelength_center.setMaximum(1000)
        self.wavelength_center.setValue(500)
        self.wavelength_center.setSingleStep(0.1)
        self.wavelength_center.setEnabled(False)

        self.wavelength_right = LabeledDoubleSpinBox()
        self.wavelength_right.setText('λ right (nm)')
        self.wavelength_right.setMinimum(0)
        self.wavelength_right.setMaximum(1000)
        self.wavelength_right.setValue(500)
        self.wavelength_right.setSingleStep(0.1)
        self.wavelength_right.setEnabled(False)

        self.spectrum_button = QPushButton('Scan spectrum')

        self.spectrum_plot = pg.plot()
        self.spectrum_plot.setLabel('left', 'Intensity (AU)')
        self.spectrum_plot.setLabel('bottom', 'Wavelength (nm)') 

        # Powermeter ----

        self.powermeter_wavelength = LabeledDoubleSpinBox()
        self.powermeter_wavelength.setText('λ (nm)')
        self.powermeter_wavelength.valueChanged.connect(self.set_powermeter_wavelength)

        self.powermeter_beam_diameter = LabeledDoubleSpinBox()
        self.powermeter_beam_diameter.setText('Beam diameter (mm)')
        self.powermeter_beam_diameter.valueChanged.connect(self.set_powermeter_beam_diameter)

        self.calibrate_total = QPushButton('Calibrate Power')
        self.calibrate_total.clicked.connect(self.calibrate_total_power)
        self.total_power = QLabel('Total power: (μW.cm⁻²)')

        self.calibrate_blue = QPushButton('Calibrate Blue Power')
        self.calibrate_blue.clicked.connect(self.calibrate_blue_power)
        self.blue_power = QLabel('Blue power: (μW.cm⁻²)')

        self.calibrate_green = QPushButton('Calibrate Green Power')
        self.calibrate_green.clicked.connect(self.calibrate_green_power)
        self.green_power = QLabel('Green power: (μW.cm⁻²)')

        self.calibrate_red = QPushButton('Calibrate Red Power')
        self.calibrate_red.clicked.connect(self.calibrate_red_power)
        self.red_power = QLabel('Red power: (μW.cm⁻²)')

    def layout_components(self) -> None:

        spectro_ctl0 = QHBoxLayout()
        spectro_ctl0.addWidget(self.integration_time)
        spectro_ctl0.addWidget(self.no_correction)
        spectro_ctl0.addWidget(self.correct_range)
        spectro_ctl0.addWidget(self.correct_noise)

        spectro_ctl1 = QHBoxLayout()
        spectro_ctl1.addWidget(self.noise_level)
        spectro_ctl1.addWidget(self.wavelength_left)
        spectro_ctl1.addWidget(self.wavelength_center)
        spectro_ctl1.addWidget(self.wavelength_right)

        total_layout = QHBoxLayout()
        total_layout.addWidget(self.calibrate_total)
        total_layout.addStretch()
        total_layout.addWidget(self.total_power)

        blue_layout = QHBoxLayout()
        blue_layout.addWidget(self.calibrate_blue)
        blue_layout.addStretch()
        blue_layout.addWidget(self.blue_power)

        green_layout = QHBoxLayout()
        green_layout.addWidget(self.calibrate_green)
        green_layout.addStretch()
        green_layout.addWidget(self.green_power)

        red_layout = QHBoxLayout()
        red_layout.addWidget(self.calibrate_red)
        red_layout.addStretch()
        red_layout.addWidget(self.red_power)

        power_ctl = QHBoxLayout()
        power_ctl.addWidget(self.powermeter_wavelength)
        power_ctl.addWidget(self.powermeter_beam_diameter)

        layout = QVBoxLayout(self)
        layout.addWidget(self.refresh_button)
        layout.addSpacing(20)
        layout.addWidget(self.spectrometers_cb)
        layout.addLayout(spectro_ctl0)
        layout.addLayout(spectro_ctl1)
        layout.addWidget(self.spectrum_button)
        layout.addWidget(self.spectrum_plot)
        layout.addSpacing(20)
        layout.addWidget(self.powermeters_cb)
        layout.addLayout(power_ctl)
        layout.addLayout(total_layout)
        layout.addLayout(blue_layout)
        layout.addLayout(green_layout)
        layout.addLayout(red_layout)
        layout.addStretch()
    
    def correct_spectrum(self):

        # clear plot 

        # enable or disable controls
        self.noise_level.setEnabled(False)
        self.wavelength_left.setEnabled(False)
        self.wavelength_center.setEnabled(False)
        self.wavelength_right.setEnabled(False)
    
        if self.correct_noise.isChecked():
            self.noise_level.setEnabled(True)
            self.wavelength_center.setEnabled(True)
        
        if self.correct_range.isChecked():
            self.wavelength_left.setEnabled(True)
            self.wavelength_right.setEnabled(True)

    def calibrate_total_power(self):
        ...

    def calibrate_blue_power(self):
        ...
        
    def calibrate_green_power(self):
        ...
        
    def calibrate_red_power(self):
        ...
        
    def set_powermeter_wavelength(self):
        ...

    def set_powermeter_beam_diameter(self):
        ...

    def refresh_devices(self) -> None:

        self.spectrometers = thorlabs_ccs.list_spectrometers()
        self.spectrometers_cb.clear()
        for dev_info in self.spectrometers:
            self.spectrometers_cb.addItem(dev_info.serial_number)
        
        self.powermeters = thorlabs_pmd.list_powermeters()
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
