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
from qt_widgets import LabeledComboBox, LabeledComboBox, LabeledDoubleSpinBox, LabeledSpinBox
from typing import Dict, TypedDict, Tuple, List
import pyqtgraph as pg
import numpy as np
from functools import partial

import thorlabs_ccs 
import thorlabs_pmd

# TODO button to save state (spectrum + power) as reference and overlay ref  
# TODO check hardware state
# TODO might get errors if things are unplugged mid-way

pg.setConfigOption('background', (251,251,251,255))
pg.setConfigOption('foreground', 'k')
pg.setConfigOption('antialias', True)


class SpectrometerState(TypedDict, total=False):
    spectrometers: List[thorlabs_ccs.DevInfo]
    serial_number: str
    integration_time: float
    no_correction: bool
    correct_range: bool
    correct_noise: bool
    noise_level: float
    wavelength_left: float
    wavelength_center: float
    wavelength_right: float
    spectrum: Tuple[np.ndarray, np.ndarray] 

class SpectrometerWidget(QWidget):

    # signals
    spectrometer_changed = pyqtSignal(int)
    integration_time_changed = pyqtSignal(float)
    scan_spectrum = pyqtSignal()

    # constants
    LINE_COL = (50,50,50,255)
    LINE_WIDTH = 2
    HEIGHT = 400
    SPECTRUM_COORD_HINT_SIZE = 7

    def __init__(self,*args,**kwargs):

        super().__init__(*args, **kwargs)

        self.spectrometers: List[thorlabs_ccs.DevInfo] = []
        self.declare_components()
        self.layout_components()
        self.refresh_devices()
        
    def declare_components(self) -> None:

        self.refresh_button = QPushButton('Refresh Spectrometers')
        self.refresh_button.clicked.connect(self.refresh_devices)

        self.spectrometers_cb = LabeledComboBox()
        self.spectrometers_cb.setText('Spectrometer')
        self.spectrometers_cb.currentIndexChanged.connect(self.spectrometer_changed)

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
        self.spectrum_plot.setXRange(200,1000)
        self.spectrum_plot.setFixedHeight(self.HEIGHT)
        self.spectrum_plot.setLabel('left', 'Intensity (AU)')
        self.spectrum_plot.setLabel('bottom', 'Wavelength (nm)') 
        self.spectrum_data = self.spectrum_plot.plot(
            np.linspace(200,1000,800), 
            np.zeros((800,)), 
            pen=pg.mkPen(self.LINE_COL, width=self.LINE_WIDTH)
        )

        self.coord_label = QLabel("Wavelength=0 nm, Intensity=0")
        self.hover_point = self.spectrum_plot.plot(
            [0], [0],
            pen=None, symbol='o', symbolBrush='r', symbolSize=self.SPECTRUM_COORD_HINT_SIZE
        )
        self.proxy = pg.SignalProxy(
            self.spectrum_plot.scene().sigMouseMoved,
            rateLimit=60,
            slot=self.mouseMoved
        )

    def layout_components(self) -> None:

        spectro_ctl1 = QHBoxLayout()
        spectro_ctl1.addWidget(self.correct_noise)
        spectro_ctl1.addWidget(self.noise_level)
        spectro_ctl1.addWidget(self.wavelength_center)
        
        spectro_ctl2 = QHBoxLayout()
        spectro_ctl2.addWidget(self.correct_range)
        spectro_ctl2.addWidget(self.wavelength_left)
        spectro_ctl2.addWidget(self.wavelength_right)

        layout = QVBoxLayout(self)
        layout.addWidget(self.refresh_button)
        layout.addSpacing(20)
        layout.addWidget(self.spectrometers_cb)
        layout.addWidget(self.integration_time)
        layout.addWidget(self.no_correction)
        layout.addLayout(spectro_ctl1)
        layout.addLayout(spectro_ctl2)
        layout.addWidget(self.spectrum_button)
        layout.addWidget(self.spectrum_plot)
        layout.addWidget(self.coord_label)
        layout.addStretch()

    def update_wavelength_left(self, value: float) -> None:
        if self.wavelength_right.value() <= value:
            self.wavelength_right.setValue(value+1)

    def update_wavelength_right(self, value: float) -> None:
        if self.wavelength_left.value() >= value:
            self.wavelength_left.setValue(value-1)

    def correct_spectrum(self):

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

    def refresh_devices(self) -> None:

        self.spectrometers = thorlabs_ccs.list_spectrometers()
        self.spectrometers_cb.clear()
        for dev_info in self.spectrometers:
            self.spectrometers_cb.addItem(dev_info.serial_number)

    def get_state(self) -> SpectrometerState:
        
        state: SpectrometerState = {
            'spectrometers': self.spectrometers,
            'serial_number': self.spectrometers_cb.currentText(),
            'integration_time': self.integration_time.value(),
            'no_correction': self.no_correction.isChecked(),
            'correct_range': self.correct_range.isChecked(),
            'correct_noise': self.correct_noise.isChecked(),
            'noise_level': self.noise_level.value(),
            'wavelength_left': self.wavelength_left.value(),
            'wavelength_center': self.wavelength_center.value(),
            'wavelength_right': self.wavelength_right.value(),
            'spectrum': self.spectrum_data.getData(),
        }
        return state

    def set_state(self, state: SpectrometerState) -> None:

        setters = {
            'serial_number': self.spectrometers_cb.setCurrentText,
            'integration_time': self.integration_time.setValue,
            'no_correction': self.no_correction.setChecked,
            'correct_range': self.correct_range.setChecked,
            'correct_noise': self.correct_noise.setChecked,
            'noise_level': self.noise_level.setValue,
            'wavelength_left': self.wavelength_left.setValue,
            'wavelength_center': self.wavelength_center.setValue,
            'wavelength_right': self.wavelength_right.setValue,
            'spectrum': self.spectrum_data.setData
        }

        for key, setter in setters.items():
            if key in state:
                setter(state[key])

    def mouseMoved(self, evt):
        pos = evt[0]  # QPointF from the scene
        if self.spectrum_plot.sceneBoundingRect().contains(pos):
            mouse_point = self.spectrum_plot.plotItem.vb.mapSceneToView(pos)
            mouse_pos = np.array((mouse_point.x(), mouse_point.y()))
            spectrum = np.array(self.spectrum_data.getData())

            dists = np.sum((mouse_pos - spectrum.T)**2, axis=1)
            idx = np.argmin(dists)
            x_closest, y_closest = spectrum[:,idx]

            self.coord_label.setText(f"Wavelength={x_closest:.2f} nm, Intensity={y_closest:.2f}")
            self.hover_point.setData([x_closest], [y_closest])

    def closeEvent(self, event):
        ...

class SpectrometerController(QObject):
    
    def __init__(self, spectrometer_widget: SpectrometerWidget, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.spectrometer_widget = spectrometer_widget
        self.spectrometer_widget.spectrometer_changed.connect(self.spectrometer_changed)
        self.spectrometer_widget.integration_time_changed.connect(self.integration_time_changed)
        self.spectrometer_widget.scan_spectrum.connect(self.scan_spectrum)

        self.spectrometer_constructor = None
        
    def spectrometer_changed(self) -> None:

        state = self.spectrometer_widget.get_state()
        
        if state['serial_number'] == '':
            return
        
        device_info = [
            dev_info 
            for dev_info in state['spectrometers'] 
            if dev_info.serial_number == state['serial_number']
        ]
        if not device_info:
            raise thorlabs_ccs.DeviceNotFound(f"Serial number: {state['serial_number']}")
        self.spectrometer_constructor = partial(thorlabs_ccs.TLCCS, device_info = device_info[0])
        
        # reset GUI
        new_state: SpectrometerState = {}
        with self.spectrometer_constructor() as spectrometer:
            new_state['integration_time'] = spectrometer.get_integration_time()*1000
        new_state['no_correction'] = True
        
        self.spectrometer_widget.set_state(new_state)

    def integration_time_changed(self, integration_time: float) -> None:

        if self.spectrometer_constructor is None:
            return
        
        with self.spectrometer_constructor() as spectrometer:
            spectrometer.set_integration_time(integration_time/1000)

    def scan_spectrum(self) -> None:
        
        state = self.spectrometer_widget.get_state()

        if self.spectrometer_constructor is None:
            return
        
        new_state: SpectrometerState = {}

        with self.spectrometer_constructor() as spectrometer:
            
            wavelength = spectrometer.get_wavelength()
            spectrometer.start_single_scan()
            
            if state['no_correction']:
                scan = spectrometer.get_scan_data_factory()

            elif state['correct_noise']:
                scan, wavelength_left, wavelength_right = spectrometer.get_scan_data_corrected_noise(
                    center_wl = state['wavelength_center'],
                    noise_amplification_dB = state['noise_level']
                )
                
                new_state['wavelength_left'] = wavelength_left 
                new_state['wavelength_right'] = wavelength_right

            else:
                scan, noise_amplification = spectrometer.get_scan_data_corrected_range(
                    min_wl = state['wavelength_left'],
                    max_wl = state['wavelength_right']
                )

                new_state['noise_level'] = noise_amplification 

            new_state['spectrum'] = (np.array(wavelength), np.array(scan))
        
        self.spectrometer_widget.set_state(new_state)   


class PowermeterState(TypedDict, total=False):
    powermeters: List[thorlabs_pmd.DevInfo]
    serial_number: str
    bandwidth_low: bool
    attenuation_dB: float
    range_decade: int
    beam_diameter_mm: float
    wavelength_red: float
    wavelength_green: float
    wavelength_blue: float
    red_power_density: float
    green_power_density: float
    blue_power_density: float

class PowermeterWidget(QWidget):

    powermeter_changed = pyqtSignal(int)
    bandwidth_changed = pyqtSignal(bool)
    attenuation_changed = pyqtSignal(float)
    range_changed = pyqtSignal(int)
    beam_diameter_changed = pyqtSignal(float)
    calibrate_red_power = pyqtSignal()
    calibrate_green_power = pyqtSignal()
    calibrate_blue_power = pyqtSignal()
    power_calibration = pyqtSignal()

    def __init__(self,*args,**kwargs):

        super().__init__(*args, **kwargs)

        self.powermeters: List[thorlabs_pmd.DevInfo] = []
        self.red_power_density: float = 0
        self.green_power_density: float = 0
        self.blue_power_density: float = 0
        
        self.declare_components()
        self.layout_components()
        self.refresh_devices()

    def declare_components(self) -> None:

        self.refresh_button = QPushButton('Refresh Powermeters')
        self.refresh_button.clicked.connect(self.refresh_devices)

        self.powermeters_cb = LabeledComboBox()
        self.powermeters_cb.setText('Powermeter')
        self.powermeters_cb.currentIndexChanged.connect(self.powermeter_changed)

        self.powermeter_low_bandwidth_chk = QCheckBox('Low Bandwidth')
        self.powermeter_low_bandwidth_chk.stateChanged.connect(self.bandwidth_changed)

        self.powermeter_attenuation_sb = LabeledDoubleSpinBox()
        self.powermeter_attenuation_sb.setText('Attenuation (dB)')
        self.powermeter_attenuation_sb.setMinimum(-60)
        self.powermeter_attenuation_sb.setMaximum(60)
        self.powermeter_attenuation_sb.setSingleStep(0.5)
        self.powermeter_attenuation_sb.setValue(0)
        self.powermeter_attenuation_sb.valueChanged.connect(self.attenuation_changed)

        self.powermeter_range_sb = LabeledSpinBox()
        self.powermeter_range_sb.setText('Range (decade)')
        self.powermeter_range_sb.setMinimum(-5)
        self.powermeter_range_sb.setMaximum(0)
        self.powermeter_range_sb.setSingleStep(1)
        self.powermeter_range_sb.setValue(-2)
        self.powermeter_range_sb.valueChanged.connect(self.range_changed)

        self.powermeter_beam_diameter = LabeledDoubleSpinBox()
        self.powermeter_beam_diameter.setText('Beam diameter (mm)')
        self.powermeter_beam_diameter.valueChanged.connect(self.beam_diameter_changed)

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

        self.full_calibration_bt = QPushButton('Power Calibration')
        self.full_calibration_bt.clicked.connect(self.power_calibration)
    
    def layout_components(self) -> None:

        blue_layout = QHBoxLayout()
        blue_layout.addWidget(self.calibrate_blue)
        blue_layout.addWidget(self.powermeter_wavelength_blue)
        blue_layout.addStretch()
        blue_layout.addWidget(self.blue_power)

        green_layout = QHBoxLayout()
        green_layout.addWidget(self.calibrate_green)
        green_layout.addWidget(self.powermeter_wavelength_green)
        green_layout.addStretch()
        green_layout.addWidget(self.green_power)

        red_layout = QHBoxLayout()
        red_layout.addWidget(self.calibrate_red)
        red_layout.addWidget(self.powermeter_wavelength_red)
        red_layout.addStretch()
        red_layout.addWidget(self.red_power)

        layout = QVBoxLayout(self)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.powermeters_cb)
        layout.addWidget(self.powermeter_beam_diameter)
        layout.addWidget(self.powermeter_low_bandwidth_chk)
        layout.addWidget(self.powermeter_range_sb)
        layout.addWidget(self.powermeter_attenuation_sb)
        layout.addLayout(blue_layout)
        layout.addLayout(green_layout)
        layout.addLayout(red_layout)
        layout.addWidget(self.full_calibration_bt)
        layout.addStretch()

    def refresh_devices(self) -> None:

        self.powermeters = thorlabs_pmd.list_powermeters()
        self.powermeters_cb.clear()
        for dev_info in self.powermeters:
            self.powermeters_cb.addItem(dev_info.serial_number)

    def set_red_power_density(self, power_density: float) -> None:
        self.red_power_density = power_density
        self.red_power.setText(f'Red power: {power_density:.3f} (mW.cm⁻²)')

    def set_green_power_density(self, power_density: float) -> None:
        self.green_power_density = power_density
        self.green_power.setText(f'Green power: {power_density:.3f} (mW.cm⁻²)')

    def set_blue_power_density(self, power_density: float) -> None:
        self.blue_power_density = power_density
        self.blue_power.setText(f'Blue power: {power_density:.3f} (mW.cm⁻²)')

    def get_state(self) -> PowermeterState:
        
        state: PowermeterState = {
            'powermeters': self.powermeters,
            'serial_number': self.powermeters_cb.currentText(),
            'attenuation_dB': self.powermeter_attenuation_sb.value(),
            'bandwidth_low': self.powermeter_low_bandwidth_chk.isChecked(),
            'range_decade': self.powermeter_range_sb.value(),
            'beam_diameter_mm': self.powermeter_beam_diameter.value(),
            'wavelength_red': self.powermeter_wavelength_red.value(),
            'wavelength_green': self.powermeter_wavelength_green.value(),
            'wavelength_blue': self.powermeter_wavelength_blue.value(),
            'red_power_density': self.red_power_density,
            'green_power_density': self.green_power_density,
            'blue_power_density': self.blue_power_density,
        }
        return state

    def set_state(self, state: PowermeterState) -> None:

        setters = {
            'serial_number': self.powermeters_cb.setCurrentText,
            'attenuation_dB': self.powermeter_attenuation_sb.setValue,
            'bandwidth_low': self.powermeter_low_bandwidth_chk.setChecked,
            'range_decade': self.powermeter_range_sb.setValue,
            'beam_diameter_mm': self.powermeter_beam_diameter.setValue,
            'wavelength_red': self.powermeter_wavelength_red.setValue,
            'wavelength_green': self.powermeter_wavelength_green.setValue,
            'wavelength_blue': self.powermeter_wavelength_blue.setValue,
            'red_power_density': self.set_red_power_density,
            'green_power_density': self.set_green_power_density,
            'blue_power_density': self.set_blue_power_density
        }

        for key, setter in setters.items():
            if key in state:
                setter(state[key])

    def closeEvent(self, event):
        ...

class PowermeterController(QObject):

    power_calibration = pyqtSignal()

    def __init__(self, powermeter_widget: PowermeterWidget, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.powermeter_constructor = None
        self.powermeter_widget = powermeter_widget
        self.powermeter_widget.powermeter_changed.connect(self.powermeter_changed)
        self.powermeter_widget.bandwidth_changed.connect(self.bandwidth_changed)
        self.powermeter_widget.attenuation_changed.connect(self.attenuation_changed)
        self.powermeter_widget.range_changed.connect(self.range_changed)
        self.powermeter_widget.beam_diameter_changed.connect(self.beam_diameter_changed)
        self.powermeter_widget.calibrate_red_power.connect(self.calibrate_red_power)
        self.powermeter_widget.calibrate_green_power.connect(self.calibrate_green_power)
        self.powermeter_widget.calibrate_blue_power.connect(self.calibrate_blue_power)
        self.powermeter_widget.power_calibration.connect(self.power_calibration)

    def powermeter_changed(self) -> None:

        state = self.powermeter_widget.get_state()

        # find powermeter with given serial number
        if state['serial_number'] == '':
            return
        
        device_info = [
            dev_info 
            for dev_info in state['powermeters'] 
            if dev_info.serial_number == state['serial_number']
        ]
        if not device_info:
            raise thorlabs_pmd.DeviceNotFound(f"Serial number: {state['serial_number']}")
        self.powermeter_constructor = partial(thorlabs_pmd.TLPMD, device_info[0])

        # reset GUI
        
        new_state: PowermeterState = {}
        with self.powermeter_constructor() as powermeter:
            new_state['beam_diameter_mm'] = self.active_powermeter.get_beam_diameter_mm()
            new_state['attenuation_dB'] = self.active_powermeter.get_attenuation_dB()
            new_state['range_decade'] = self.active_powermeter.get_current_range_decade()
            new_state['bandwidth_low'] = self.active_powermeter.get_bandwidth() == thorlabs_pmd.Bandwidth.LOW
        self.powermeter_widget.set_state(new_state)

    def attenuation_changed(self, attenuation_dB: float) -> None:

        if self.powermeter_constructor is None:
            return 
        
        with self.powermeter_constructor() as powermeter:
            powermeter.set_attenuation_dB(attenuation_dB)

    def bandwidth_changed(self, bandwidth: bool) -> None:

        if self.powermeter_constructor is None:
            return 
        
        with self.powermeter_constructor() as powermeter:
            if bandwidth:
                powermeter.set_attenuation_dB(thorlabs_pmd.Bandwidth.LOW)
            else:
                powermeter.set_attenuation_dB(thorlabs_pmd.Bandwidth.HIGH)

    def range_changed(self, range_decade: int) -> None

        if self.powermeter_constructor is None:
            return 
        
        with self.powermeter_constructor() as powermeter:
            powermeter.set_current_range_decade(range_decade)

    def beam_diameter_changed(self, beam_diameter_mm: float) -> None:

        if self.powermeter_constructor is None:
            return 
        
        with self.powermeter_constructor() as powermeter:
            powermeter.set_beam_diameter_mm(beam_diameter_mm)

    def calibrate_red_power(self) -> None:
        
        if self.powermeter_constructor is None:
            return 
        
        state = self.powermeter_widget.get_state()
        new_state: PowermeterState = {}
        with self.powermeter_constructor() as powermeter:
            powermeter.set_wavelength_nm(state['wavelength_red'])
            new_state['red_power_density'] = powermeter.get_power_density_mW_cm2()
        self.powermeter_widget.set_state(new_state)

    def calibrate_green_power(self) -> None:
        
        if self.powermeter_constructor is None:
            return 
        
        state = self.powermeter_widget.get_state()
        new_state: PowermeterState = {}
        with self.powermeter_constructor() as powermeter:
            powermeter.set_wavelength_nm(state['wavelength_green'])
            new_state['green_power_density'] = powermeter.get_power_density_mW_cm2()
        self.powermeter_widget.set_state(new_state)

    def calibrate_blue_power(self) -> None:
        
        if self.powermeter_constructor is None:
            return 
        
        state = self.powermeter_widget.get_state()
        new_state: PowermeterState = {}
        with self.powermeter_constructor() as powermeter:
            powermeter.set_wavelength_nm(state['wavelength_blue'])
            new_state['blue_power_density'] = powermeter.get_power_density_mW_cm2()
        self.powermeter_widget.set_state(new_state)

class LightAnalysisWidget2(QWidget):

    power_calibration = pyqtSignal()

    def __init__(self,*args,**kwargs):

        super().__init__(*args, **kwargs)

        self.declare_components()
        self.layout_components()

    def declare_components(self) -> None:

        self.spectrometer_widget = SpectrometerWidget()
        self.spectrometer_controller = SpectrometerController(self.spectrometer_widget) 
        
        self.powermeter_widget = PowermeterWidget()
        self.powermeter_widget = PowermeterController(self.powermeter_widget)
        self.powermeter_widget.power_calibration.connect(self.power_calibration)

    def layout_components(self) -> None:

        layout = QVBoxLayout(self)
        layout.addWidget(self.spectrometer_widget)
        layout.addWidget(self.powermeter_widget)
        layout.addStretch()

    def get_state(self) -> Dict:
        state = {}
        state['spectrometer'] = self.spectrometer_widget.get_state()
        state['powermeter'] = self.powermeter_widget.get_state()
        return state

    def set_state(self, state: Dict):
        setters = {
            'spectrometer': self.spectrometer_widget.set_state,
            'powermeter': self.powermeter_widget.set_state,
        }

        for key, setter in setters.items():
            if key in state:
                setter(state[key])

class LightAnalysisWidget(QWidget):

    LINE_COL = (50,50,50,255)
    LINE_WIDTH = 2
    LINE_COL_TEMP = (120,120,120,255)
    LINE_WIDTH_TEMP = 1
    HEIGHT = 400
    SPECTRUM_COORD_HINT_SIZE = 7

    def __init__(self,*args,**kwargs):

        super().__init__(*args, **kwargs)
        
        self.active_spectrometer = None
        self.active_powermeter = None

        self.declare_components()
        self.layout_components()
        self.refresh_devices()
    
    def declare_components(self) -> None:

        self.refresh_button = QPushButton('Refresh Light Analysis Devices')
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
        self.spectrum_plot.setXRange(200,1000)
        self.spectrum_plot.setFixedHeight(self.HEIGHT)
        self.spectrum_plot.setLabel('left', 'Intensity (AU)')
        self.spectrum_plot.setLabel('bottom', 'Wavelength (nm)') 
        self.spectrum_data = self.spectrum_plot.plot(
            np.linspace(200,1000,800), 
            np.zeros((800,)), 
            pen=pg.mkPen(self.LINE_COL, width=self.LINE_WIDTH)
        )

        self.coord_label = QLabel("Wavelength=0 nm, Intensity=0")
        self.hover_point = self.spectrum_plot.plot(
            [0], [0],
            pen=None, symbol='o', symbolBrush='r', symbolSize=self.SPECTRUM_COORD_HINT_SIZE
        )
        self.proxy = pg.SignalProxy(
            self.spectrum_plot.scene().sigMouseMoved,
            rateLimit=60,
            slot=self.mouseMoved
        )

        # Powermeter ---- 

        self.powermeter_low_bandwidth_chk = QCheckBox('Low Bandwidth')
        self.powermeter_low_bandwidth_chk.stateChanged.connect(self.set_powermeter_bandwidth)

        self.powermeter_attenuation_sb = LabeledDoubleSpinBox()
        self.powermeter_attenuation_sb.setText('Attenuation (dB)')
        self.powermeter_attenuation_sb.setMinimum(-60)
        self.powermeter_attenuation_sb.setMaximum(60)
        self.powermeter_attenuation_sb.setSingleStep(0.5)
        self.powermeter_attenuation_sb.setValue(0)
        self.powermeter_attenuation_sb.valueChanged.connect(self.set_powermeter_attenuation)

        self.powermeter_range_sb = LabeledSpinBox()
        self.powermeter_range_sb.setText('Range (decade)')
        self.powermeter_range_sb.setMinimum(-5)
        self.powermeter_range_sb.setMaximum(0)
        self.powermeter_range_sb.setSingleStep(1)
        self.powermeter_range_sb.setValue(-2)
        self.powermeter_range_sb.valueChanged.connect(self.set_powermeter_range)

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

        spectro_ctl1 = QHBoxLayout()
        spectro_ctl1.addWidget(self.correct_noise)
        spectro_ctl1.addWidget(self.noise_level)
        spectro_ctl1.addWidget(self.wavelength_center)
        
        spectro_ctl2 = QHBoxLayout()
        spectro_ctl2.addWidget(self.correct_range)
        spectro_ctl2.addWidget(self.wavelength_left)
        spectro_ctl2.addWidget(self.wavelength_right)

        blue_layout = QHBoxLayout()
        blue_layout.addWidget(self.calibrate_blue)
        blue_layout.addWidget(self.powermeter_wavelength_blue)
        blue_layout.addStretch()
        blue_layout.addWidget(self.blue_power)

        green_layout = QHBoxLayout()
        green_layout.addWidget(self.calibrate_green)
        green_layout.addWidget(self.powermeter_wavelength_green)
        green_layout.addStretch()
        green_layout.addWidget(self.green_power)

        red_layout = QHBoxLayout()
        red_layout.addWidget(self.calibrate_red)
        red_layout.addWidget(self.powermeter_wavelength_red)
        red_layout.addStretch()
        red_layout.addWidget(self.red_power)

        layout = QVBoxLayout(self)
        layout.addWidget(self.refresh_button)
        layout.addSpacing(20)
        layout.addWidget(self.spectrometers_cb)
        layout.addWidget(self.integration_time)
        layout.addWidget(self.no_correction)
        layout.addLayout(spectro_ctl1)
        layout.addLayout(spectro_ctl2)
        layout.addWidget(self.spectrum_button)
        layout.addWidget(self.spectrum_plot)
        layout.addWidget(self.coord_label)
        layout.addSpacing(20)
        layout.addWidget(self.powermeters_cb)
        layout.addWidget(self.powermeter_beam_diameter)
        layout.addWidget(self.powermeter_low_bandwidth_chk)
        layout.addWidget(self.powermeter_range_sb)
        layout.addWidget(self.powermeter_attenuation_sb)
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

    def set_powermeter_bandwidth(self):
        
        if self.active_powermeter is None:
            return
        
        if self.powermeter_low_bandwidth_chk.isChecked():
            self.active_powermeter.set_bandwidth(thorlabs_pmd.Bandwidth.LOW)
        else:
            self.active_powermeter.set_bandwidth(thorlabs_pmd.Bandwidth.HIGH)

    def set_powermeter_range(self):
        
        if self.active_powermeter is None:
            return
        
        range = self.powermeter_range_sb.value()
        self.active_powermeter.set_current_range_decade(range)

    def set_powermeter_attenuation(self):
        
        if self.active_powermeter is None:
            return
        
        attenuation = self.powermeter_attenuation_sb.value()
        self.active_powermeter.set_attenuation_dB(attenuation)

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

        attenuation = self.active_powermeter.get_attenuation_dB()
        self.powermeter_attenuation_sb.blockSignals(True)
        self.powermeter_attenuation_sb.setValue(attenuation)
        self.powermeter_attenuation_sb.blockSignals(False)

        range = self.active_powermeter.get_current_range_decade()
        self.powermeter_range_sb.blockSignals(True)
        self.powermeter_range_sb.setValue(range)
        self.powermeter_range_sb.blockSignals(False)

        bandwidth = self.active_powermeter.get_bandwidth()
        self.powermeter_low_bandwidth_chk.blockSignals(True)
        if bandwidth == thorlabs_pmd.Bandwidth.LOW:
            self.powermeter_low_bandwidth_chk.setChecked(True)
        else:
            self.powermeter_low_bandwidth_chk.setChecked(False)
        self.powermeter_low_bandwidth_chk.blockSignals(False)

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

    def mouseMoved(self, evt):
        pos = evt[0]  # QPointF from the scene
        if self.spectrum_plot.sceneBoundingRect().contains(pos):
            mouse_point = self.spectrum_plot.plotItem.vb.mapSceneToView(pos)
            mouse_pos = np.array((mouse_point.x(), mouse_point.y()))
            spectrum = np.array(self.spectrum_data.getData())

            dists = np.sum((mouse_pos - spectrum.T)**2, axis=1)
            idx = np.argmin(dists)
            x_closest, y_closest = spectrum[:,idx]

            self.coord_label.setText(f"Wavelength={x_closest:.2f} nm, Intensity={y_closest:.2f}")
            self.hover_point.setData([x_closest], [y_closest])

    def closeEvent(self, event):
        
        if self.active_powermeter is not None:
            self.active_powermeter.close()
        
        if self.active_spectrometer is not None:
            self.active_spectrometer.close()

if __name__ == '__main__':

    app = QApplication([])
    window = LightAnalysisWidget()
    window.show()
    app.exec()
