from ds18b20 import read_temperature_celsius, CommunicationError
from dagline import WorkerNode
import time
from typing import Any

class TemperatureLoggerWorker(WorkerNode):

    def __init__(
            self, 
            filename: str = 'temperature.csv',
            serial_port: str = '/dev/ttyUSB0',
            *args, 
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.filename = filename
        self.serial_port = serial_port
        self.fd = None

    def set_filename(self, filename:str):
        self.filename = filename

    def initialize(self) -> None:
        super().initialize()
        self.fd = open(self.filename, 'w')
        headers = ('timestamp', 'temperature_celsius')
        self.fd.write(','.join(headers) + '\n')

    def cleanup(self):
        super().cleanup()
        self.fd.close()

    def process_data(self, data) -> None:

        try:
            temperature = read_temperature_celsius(port=self.serial_port)
        except CommunicationError as e:
            print(e)
            return

        timestamp = time.perf_counter_ns()
        self.fd.write(f"{timestamp}, {temperature}\n")

    def process_metadata(self, metadata) -> Any:
        pass