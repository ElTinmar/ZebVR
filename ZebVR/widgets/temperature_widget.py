from PyQt5.QtWidgets import (
    QApplication,
    QWidget, 
    QVBoxLayout,
    QLabel,
    QComboBox,
    QPushButton
)
from PyQt5.QtCore import QRunnable, QThreadPool, QTimer, pyqtSignal
import pyqtgraph as pg
from collections import deque
import os
from typing import Dict

from ..serial_utils import list_serial_devices, SerialDevice
from ds18b20 import read_temperature_celsius
from qt_widgets import LabeledEditLine

pg.setConfigOption('background', (251,251,251,255))
pg.setConfigOption('foreground', 'k')
pg.setConfigOption('antialias', True)

class TemperatureWidget(QWidget):

    state_changed = pyqtSignal()

    N_TIME_POINTS = 600
    REFRESH_RATE_TEMPERATURE = 1  
    TARGET_TEMPERATURE = 28.0
    ACCEPTABLE_RANGE = 1.0
    TEMP_RANGE = (16,34)
    HEIGHT = 400
    LINE_COL = (50,50,50,255)
    LINE_WIDTH = 2
    TARGET_COL = (0,255,0,100)
    CSV_FOLDER: str = 'output/data'

    def __init__(self,*args,**kwargs):

        super().__init__(*args, **kwargs)
        self.current_temperature = 0.0
        self.temperature = deque(maxlen=self.N_TIME_POINTS)
        self.serial_devices = [SerialDevice()] + list_serial_devices()
        self.thread_pool = QThreadPool()
        self.monitor = None
        self.filename = ''

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_temperature)
        self.timer.start(int(1000/self.REFRESH_RATE_TEMPERATURE)) 

        self.declare_components()
        self.layout_components()
    
    def declare_components(self) -> None:
        
        self.edt_filename = LabeledEditLine()
        self.edt_filename.setLabel('temperature file:')
        self.edt_filename.setText('temperature.csv')
        self.edt_filename.textChanged.connect(self.state_changed)

        self.refresh = QPushButton('Refresh serial devices')
        self.refresh.clicked.connect(self.refresh_serial)

        self.serial_ports = QComboBox()
        self.serial_ports.currentIndexChanged.connect(self.serial_changed)
        for ser_port, description in self.serial_devices:
            self.serial_ports.addItem(f"{ser_port} - {description}")

        self.temperature_label = QLabel()

        self.temperature_curve = pg.plot()
        self.temperature_curve.setFixedHeight(self.HEIGHT)
        self.temperature_curve.setYRange(*self.TEMP_RANGE)
        self.temperature_curve.setXRange(0,self.N_TIME_POINTS)
        self.temperature_curve.setLabel('left', 'Temperature (\N{DEGREE SIGN}C)')

        target_temp_zone = pg.LinearRegionItem(
            values = [self.TARGET_TEMPERATURE-self.ACCEPTABLE_RANGE, self.TARGET_TEMPERATURE+self.ACCEPTABLE_RANGE], 
            pen = self.TARGET_COL,
            brush = self.TARGET_COL,
            orientation = 'horizontal'
        )
        self.temperature_curve.addItem(target_temp_zone)
        self.temperature_curve_data = self.temperature_curve.plot(pen=pg.mkPen(self.LINE_COL, width=self.LINE_WIDTH))

    def serial_changed(self, index) -> None:
        self.state_changed.emit()
        port = self.serial_devices[index].device
        if port == '':
            self.stop_monitor()
            return 
        
        self.monitor = TemperatureMonitor(self, port=port)
        self.thread_pool.start(self.monitor)

    def layout_components(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self.edt_filename)
        layout.addWidget(self.refresh)
        layout.addWidget(self.serial_ports)
        layout.addWidget(self.temperature_label)
        layout.addWidget(self.temperature_curve)
        layout.addStretch()

    def stop_monitor(self) -> None:
        if self.monitor is not None: 
            self.monitor.stop()
        self.monitor = None

    def set_temperature(self, temp: float) -> None:
        self.current_temperature = temp
        self.temperature.append(temp)
        
    def show_temperature(self) -> None:
        self.temperature_label.setText(f"temperature: {self.current_temperature:.2f}\N{DEGREE SIGN}C")
        self.temperature_curve_data.setData(self.temperature)

    def refresh_serial(self):
        self.stop_monitor()
        self.serial_devices = [SerialDevice()] + list_serial_devices()
        self.serial_ports.clear()
        for ser_port, description in self.serial_devices:
            self.serial_ports.addItem(f"{ser_port} - {description}")

    def set_prefix(self, prefix: str) -> None:
        self.filename = os.path.join(self.CSV_FOLDER, f'temperature_{prefix}.csv')
        self.edt_filename.setText(self.filename)
        self.state_changed.emit()

    def get_state(self) -> Dict:
        index = self.serial_ports.currentIndex()
        port = self.serial_devices[index].device

        state = {}
        state['csv_filename'] = self.edt_filename.text()
        state['serial_port'] = port
        return state
    
    def set_state(self, state: Dict) -> None:

        setters = {
            'csv_filename': self.edt_filename.setText
        }
        
        for key, setter in setters.items():
            if key in state:
                setter(state[key])

    def closeEvent(self, event):
        self.stop_monitor()

class TemperatureMonitor(QRunnable):

    def __init__(
            self, 
            widget: TemperatureWidget, 
            port: str,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.widget = widget
        self.port = port
        self.keepgoing = True
    
    def stop(self):
        self.keepgoing = False
    
    def run(self):
        while self.keepgoing:
            try:
                temperature = read_temperature_celsius(port = self.port)
                self.widget.set_temperature(temperature)
            except Exception as e:
                print(e)
            
if __name__ == "__main__":

    app = QApplication([])
    window = TemperatureWidget()
    window.show()
    app.exec()
