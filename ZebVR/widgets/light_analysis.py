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
from PyQt5.QtCore import pyqtSignal, QObject, QThread, QTimer, Qt
from qt_widgets import LabeledComboBox, LabeledComboBox, LabeledDoubleSpinBox
from typing import Dict
import pyqtgraph as pg

import thorlabs_ccs 
import thorlabs_pmd

# TODO overlay reference scan 
# TODO check hardware state

pg.setConfigOption('background', (251,251,251,255))
pg.setConfigOption('foreground', 'k')
pg.setConfigOption('antialias', True)

class LightAnalysisWidget(QWidget):

    LINE_COL = (50,50,50,255)
    LINE_WIDTH = 2
    LINE_COL_TEMP = (120,120,120,255)
    LINE_WIDTH_TEMP = 1

    def __init__(self,*args,**kwargs):

        super().__init__(*args, **kwargs)
        
        self.active_spectrometer = None
        self.active_powermeter = None

        self.declare_components()
        self.layout_components()
        self.refresh_devices()
    
    def declare_components(self) -> None:

        self.refresh_button = QPushButton('Refresh Devices')
        self.refresh_button.clicked.connect(self.refresh_devices)

        # Spectrometer ----

        self.spectrometers_cb = LabeledComboBox()
        self.spectrometers_cb.setText('Spectrometer')
        self.spectrometers_cb.currentIndexChanged.connect(self.spectrometer_changed)
        
        self.powermeters_cb = LabeledComboBox()
        self.powermeters_cb.setText('Powermeter')
        self.powermeters_cb.currentIndexChanged.connect(self.powermeter_changed)

        self.integration_time = LabeledDoubleSpinBox()
        self.integration_time.setText('Integration time (ms)')
        self.integration_time.setMinimum(thorlabs_ccs.TLCCS_MIN_INT_TIME*1000)
        self.integration_time.setMaximum(thorlabs_ccs.TLCCS_MAX_INT_TIME*1000)
        self.integration_time.setValue(thorlabs_ccs.TLCCS_DEF_INT_TIME*1000)
        self.integration_time.setSingleStep(0.01)
        self.integration_time.valueChanged.connect(self.integration_time_changed)

        self.no_correction = QCheckBox('No correction')
        self.no_correction.setChecked(True)
        self.no_correction.stateChanged.connect(self.correct_spectrum)
        
        self.correct_range = QCheckBox('Correct range')
        self.correct_range.setChecked(False)
        self.correct_range.stateChanged.connect(self.correct_spectrum)
        
        self.correct_noise = QCheckBox('Correct noise')
        self.correct_noise.setChecked(False)
        self.correct_noise.stateChanged.connect(self.correct_spectrum)

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
        self.wavelength_left.setValue(320)
        self.wavelength_left.setSingleStep(0.1)
        self.wavelength_left.setEnabled(False)
        self.wavelength_left.valueChanged.connect(self.update_wavelength_left)

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
        self.wavelength_right.setValue(720)
        self.wavelength_right.setSingleStep(0.1)
        self.wavelength_right.setEnabled(False)
        self.wavelength_right.valueChanged.connect(self.update_wavelength_right)

        self.spectrum_button = QPushButton('Scan spectrum')
        self.spectrum_button.clicked.connect(self.scan_spectrum)

        self.spectrum_plot = pg.plot()
        self.spectrum_plot.setLabel('left', 'Intensity (AU)')
        self.spectrum_plot.setLabel('bottom', 'Wavelength (nm)') 
        self.spectrum_data = self.spectrum_plot.plot(pen=pg.mkPen(self.LINE_COL, width=self.LINE_WIDTH))

        # Powermeter ---- 

        self.powermeter_beam_diameter = LabeledDoubleSpinBox()
        self.powermeter_beam_diameter.setText('Beam diameter (mm)')
        self.powermeter_beam_diameter.valueChanged.connect(self.set_powermeter_beam_diameter)

        self.calibrate_blue = QPushButton('Calibrate Blue Power')
        self.calibrate_blue.clicked.connect(self.calibrate_blue_power)
        self.blue_power = QLabel('Blue power: (mW.cm⁻²)')
        self.powermeter_wavelength_blue = LabeledDoubleSpinBox()
        self.powermeter_wavelength_blue.setText('λ (nm)')
        self.powermeter_wavelength_blue.setMinimum(0)
        self.powermeter_wavelength_blue.setMaximum(2000)
        self.powermeter_wavelength_blue.setValue(450)

        self.calibrate_green = QPushButton('Calibrate Green Power')
        self.calibrate_green.clicked.connect(self.calibrate_green_power)
        self.green_power = QLabel('Green power: (mW.cm⁻²)')
        self.powermeter_wavelength_green = LabeledDoubleSpinBox()
        self.powermeter_wavelength_green.setText('λ (nm)')
        self.powermeter_wavelength_green.setMinimum(0)
        self.powermeter_wavelength_green.setMaximum(2000)
        self.powermeter_wavelength_green.setValue(535)

        self.calibrate_red = QPushButton('Calibrate Red Power')
        self.calibrate_red.clicked.connect(self.calibrate_red_power)
        self.red_power = QLabel('Red power: (mW.cm⁻²)')
        self.powermeter_wavelength_red = LabeledDoubleSpinBox()
        self.powermeter_wavelength_red.setText('λ (nm)')
        self.powermeter_wavelength_red.setMinimum(0)
        self.powermeter_wavelength_red.setMaximum(2000)
        self.powermeter_wavelength_red.setValue(675)

    def layout_components(self) -> None:

        spectro_ctl0 = QHBoxLayout()
        spectro_ctl0.addWidget(self.integration_time)
        spectro_ctl0.addSpacing(10)
        spectro_ctl0.addWidget(self.no_correction)
        spectro_ctl0.addWidget(self.correct_range)
        spectro_ctl0.addWidget(self.correct_noise)

        spectro_ctl1 = QHBoxLayout()
        spectro_ctl1.addWidget(self.noise_level)
        spectro_ctl1.addSpacing(5)
        spectro_ctl1.addWidget(self.wavelength_left)
        spectro_ctl1.addSpacing(5)
        spectro_ctl1.addWidget(self.wavelength_center)
        spectro_ctl1.addSpacing(5)
        spectro_ctl1.addWidget(self.wavelength_right)

        blue_layout = QHBoxLayout()
        blue_layout.addWidget(self.calibrate_blue)
        blue_layout.addSpacing(10)
        blue_layout.addWidget(self.powermeter_wavelength_blue)
        blue_layout.addStretch()
        blue_layout.addWidget(self.blue_power)

        green_layout = QHBoxLayout()
        green_layout.addWidget(self.calibrate_green)
        green_layout.addSpacing(10)
        green_layout.addWidget(self.powermeter_wavelength_green)
        green_layout.addStretch()
        green_layout.addWidget(self.green_power)

        red_layout = QHBoxLayout()
        red_layout.addWidget(self.calibrate_red)
        red_layout.addSpacing(10)
        red_layout.addWidget(self.powermeter_wavelength_red)
        red_layout.addStretch()
        red_layout.addWidget(self.red_power)

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
        layout.addWidget(self.powermeter_beam_diameter)
        layout.addLayout(blue_layout)
        layout.addLayout(green_layout)
        layout.addLayout(red_layout)
        layout.addStretch()
    
    def correct_spectrum(self):

        # clear plot 
        self.spectrum_data.setPen(pg.mkPen(self.LINE_COL_TEMP, width=self.LINE_WIDTH_TEMP))

        # enable or disable controls
        if self.no_correction.isChecked():
            self.noise_level.setEnabled(False)
            self.wavelength_left.setEnabled(False)
            self.wavelength_center.setEnabled(False)
            self.wavelength_right.setEnabled(False)
    
        if self.correct_noise.isChecked():
            self.noise_level.setEnabled(True)
            self.wavelength_center.setEnabled(True)
            self.wavelength_left.setEnabled(False)
            self.wavelength_right.setEnabled(False)
        
        if self.correct_range.isChecked():
            self.noise_level.setEnabled(False)
            self.wavelength_center.setEnabled(False)
            self.wavelength_left.setEnabled(True)
            self.wavelength_right.setEnabled(True)
    
    def scan_spectrum(self):
        
        if self.active_spectrometer is None:
            return
        
        wavelength = self.active_spectrometer.get_wavelength()
        self.active_spectrometer.start_single_scan()
        
        if self.no_correction.isChecked():
            scan = self.active_spectrometer.get_scan_data_factory()

        if self.correct_noise.isChecked():
            center_wl = self.wavelength_center.value()
            noise_amplification = self.noise_level.value()
            scan, wavelength_left, wavelength_right = self.active_spectrometer.get_scan_data_corrected_noise(
                center_wl = center_wl,
                noise_amplification_dB = noise_amplification
            )
            
            self.wavelength_left.blockSignals(True)
            self.wavelength_left.setValue(wavelength_left)
            self.wavelength_left.blockSignals(False)

            self.wavelength_right.blockSignals(True)
            self.wavelength_right.setValue(wavelength_right)
            self.wavelength_right.blockSignals(False)

        if self.correct_range.isChecked():
            wavelength_left = self.wavelength_left.value()
            wavelength_right = self.wavelength_right.value()
            scan, noise_amplification = self.active_spectrometer.get_scan_data_corrected_range(
                min_wl = wavelength_left,
                max_wl = wavelength_right
            )

            self.noise_level.blockSignals(True)
            self.noise_level.setValue(noise_amplification)
            self.noise_level.blockSignals(False)

            #TODO Should I update wavelength center as well?

        self.spectrum_data.setPen(pg.mkPen(self.LINE_COL, width=self.LINE_WIDTH))
        self.spectrum_data.setData(wavelength, scan)

    def update_wavelength_left(self, value: float) -> None:
        if self.wavelength_right.value() <= value:
            self.wavelength_right.setValue(value+1)

    def update_wavelength_right(self, value: float) -> None:
        if self.wavelength_left.value() >= value:
            self.wavelength_left.setValue(value-1)

    def calibrate_blue_power(self):
        # TODO show blue screen on projector. Maybe emit signal?
        
        if self.active_powermeter is None:
            return
        
        wavelength = self.powermeter_wavelength_blue.value()
        self.active_powermeter.set_wavelength_nm(wavelength)
        power = self.active_powermeter.get_power_density_mW_cm2()
        self.blue_power.setText(f'Blue power: {power:.3f} (mW.cm⁻²)')
        
    def calibrate_green_power(self):
        # TODO show green screen on projector. Maybe emit signal?
        
        if self.active_powermeter is None:
            return
        
        wavelength = self.powermeter_wavelength_green.value()
        self.active_powermeter.set_wavelength_nm(wavelength)
        power = self.active_powermeter.get_power_density_mW_cm2()
        self.green_power.setText(f'Green power: {power:.3f} (mW.cm⁻²)')
        
    def calibrate_red_power(self):
        # TODO show red screen on projector. Maybe emit signal?
        
        if self.active_powermeter is None:
            return
        
        wavelength = self.powermeter_wavelength_red.value()
        self.active_powermeter.set_wavelength_nm(wavelength)
        power = self.active_powermeter.get_power_density_mW_cm2()
        self.red_power.setText(f'Red power: {power:.3f} (mW.cm⁻²)')
        
    def set_powermeter_beam_diameter(self):
        
        if self.active_powermeter is None:
            return
        
        beam_diameter = self.powermeter_beam_diameter.value()
        self.active_powermeter.set_beam_diameter_mm(beam_diameter)

    def integration_time_changed(self):

        if self.active_spectrometer is None:
            return
        
        integration_time = self.integration_time.value()
        self.active_spectrometer.set_integration_time(integration_time/1000)

    def spectrometer_changed(self):

        # find spectro with given serial number
        serial_number = self.spectrometers_cb.currentText()
        if serial_number == '':
            return
        
        device_info = [dev_info for dev_info in self.spectrometers if dev_info.serial_number == serial_number]
        if not device_info:
            raise thorlabs_ccs.DeviceNotFound(f'Serial number: {serial_number}')
        self.active_spectrometer = thorlabs_ccs.TLCCS(device_info[0])
        
        # reset GUI
        integration_time = self.active_spectrometer.get_integration_time()*1000
        self.integration_time.blockSignals(True)
        self.integration_time.setValue(integration_time)
        self.integration_time.blockSignals(False)

        self.no_correction.setChecked(True)

    def powermeter_changed(self):
        
        # find powermeter with given serial number
        serial_number = self.powermeters_cb.currentText()
        if serial_number == '':
            return
        
        device_info = [dev_info for dev_info in self.powermeters if dev_info.serial_number == serial_number]
        if not device_info:
            raise thorlabs_pmd.DeviceNotFound(f'Serial number: {serial_number}')
        self.active_powermeter = thorlabs_pmd.TLPMD(device_info[0])

        # reset GUI
        beam_diameter = self.active_powermeter.get_beam_diameter_mm()
        self.powermeter_beam_diameter.blockSignals(True)
        self.powermeter_beam_diameter.setValue(beam_diameter)
        self.powermeter_beam_diameter.blockSignals(False)

    def refresh_devices(self) -> None:

        # spectrometer ---------

        if self.active_spectrometer is not None:
            try:
                self.active_spectrometer.close()
            except:
                pass
            self.active_spectrometer = None

        self.spectrometers = thorlabs_ccs.list_spectrometers()
        self.spectrometers_cb.clear()
        for dev_info in self.spectrometers:
            self.spectrometers_cb.addItem(dev_info.serial_number)
        
        # powermeter ------------

        if self.active_powermeter is not None:
            try:
                self.active_powermeter.close()
            except:
                pass
            self.active_powermeter = None

        self.powermeters = thorlabs_pmd.list_powermeters()
        self.powermeters_cb.clear()
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
