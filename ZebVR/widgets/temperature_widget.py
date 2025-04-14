from PyQt5.QtWidgets import (
    QApplication,
    QWidget, 
    QVBoxLayout,
    QLabel,
    QComboBox
)
from PyQt5.QtCore import QRunnable, QThreadPool, QTimer
import pyqtgraph as pg
from collections import deque

from ..serial_utils import list_serial_devices, SerialDevice
from ds18b20 import read_temperature_celsius

pg.setConfigOption('background', (251,251,251,255))
pg.setConfigOption('foreground', 'k')
pg.setConfigOption('antialias', True)

# TODO add log file?
class TemperatureWidget(QWidget):

    N_TIME_POINTS = 100
    REFRESH_RATE = 1  
    TARGET_TEMPERATURE = 28.0
    ACCEPTABLE_RANGE = 1.0

    def __init__(self,*args,**kwargs):

        super().__init__(*args, **kwargs)
        self.current_temperature = 0.0
        self.temperature = deque(maxlen=self.N_TIME_POINTS)
        self.serial_devices = [SerialDevice()] + list_serial_devices()
        self.thread_pool = QThreadPool()
        self.monitor = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.show_temperature)
        self.timer.start(int(1000/self.REFRESH_RATE)) 

        self.declare_components()
        self.layout_components()
    
    def declare_components(self) -> None:

        self.serial_ports = QComboBox()
        self.serial_ports.currentIndexChanged.connect(self.serial_changed)
        for ser_port, description in self.serial_devices:
            self.serial_ports.addItem(f"{ser_port} - {description}")

        self.temperature_label = QLabel()

        self.temperature_curve = pg.plot()
        self.temperature_curve.setFixedHeight(400)
        self.temperature_curve.setYRange(15,35)
        self.temperature_curve.setXRange(0,self.N_TIME_POINTS)
        self.temperature_curve.setLabel('left', 'Temperature (\N{DEGREE SIGN}C)')

        target_temp_zone = pg.LinearRegionItem(
            values = [self.TARGET_TEMPERATURE-self.ACCEPTABLE_RANGE, self.TARGET_TEMPERATURE+self.ACCEPTABLE_RANGE], 
            pen = (0,255,0,100),
            brush = (0,255,0,100),
            orientation = 'horizontal'
        )
        self.temperature_curve.addItem(target_temp_zone)
        self.temperature_curve_data = self.temperature_curve.plot(pen=pg.mkPen((50,50,50,255), width=2))

    def serial_changed(self, index) -> None:
        port = self.serial_devices[index].device
        if port == '':
            self.stop_monitor()
            return 
        
        self.monitor = TemperatureMonitor(self, port=port)
        self.thread_pool.start(self.monitor)

    def layout_components(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(self.serial_ports)
        layout.addWidget(self.temperature_label)
        layout.addWidget(self.temperature_curve)
        layout.addStretch()

    def stop_monitor(self) -> None:
        if self.monitor is not None: 
            self.monitor.stop()
        self.thread_pool.waitForDone(-1)

    def set_temperature(self, temp: float) -> None:
        self.current_temperature = temp
        self.temperature.append(temp)
        
    def show_temperature(self) -> None:
        self.temperature_label.setText(f"temprerature: {self.current_temperature:.2f}\N{DEGREE SIGN}C")
        self.temperature_curve_data.setData(self.temperature)

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
            temperature = read_temperature_celsius(port = self.port)
            self.widget.set_temperature(temperature)

if __name__ == "__main__":

    app = QApplication([])
    window = TemperatureWidget()
    window.show()
    app.exec()
