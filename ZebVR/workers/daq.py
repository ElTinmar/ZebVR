from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional, List
from daq_tools import Arduino_SoftTiming, LabJackU3_SoftTiming, NI_SoftTiming

# TODO work in prog
class DAQ_Worker(WorkerNode):

    def __init__(
            self, 
            arduino_ports: List,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)

    def initialize(self) -> None:
        super().initialize()
        
    def cleanup(self) -> None:
        super().cleanup()
    
    def process_data(self, data) -> NDArray:
        pass

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        pass
        