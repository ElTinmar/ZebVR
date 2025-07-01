from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional, List, Union
from daq_tools import Arduino_SoftTiming, LabJackU3_SoftTiming, NI_SoftTiming

# TODO work in progress

class DAQ_Worker(WorkerNode):

    def __init__(
            self, 
            arduino_IDs: List[Union[int, str]],
            labjack_IDs: List[Union[int, str]],
            national_instruments_IDs: List[Union[int, str]],
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.arduino_IDs = arduino_IDs
        self.labjack_IDs = labjack_IDs
        self.national_instruments_IDs = national_instruments_IDs

    def initialize(self) -> None:

        super().initialize()
        self.arduinos = [Arduino_SoftTiming(board_id) for board_id in self.arduino_IDs]
        self.labjacks = [LabJackU3_SoftTiming(board_id) for board_id in self.labjack_IDs]
        self.nis = [NI_SoftTiming(board_id) for board_id in self.national_instruments_IDs]

    def cleanup(self) -> None:
        
        super().cleanup()

        for arduino in self.arduinos:
            arduino.close()
    
        for labjack in self.labjacks:
            labjack.close()
    
        for ni in self.nis:
            ni.close()

    def process_data(self, data) -> NDArray:
        pass

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        pass
        