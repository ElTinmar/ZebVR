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
        self.arduinos = {board_id: Arduino_SoftTiming(board_id) for board_id in self.arduino_IDs}
        self.labjacks = {board_id: LabJackU3_SoftTiming(board_id) for board_id in self.labjack_IDs}
        self.nis = {board_id: NI_SoftTiming(board_id) for board_id in self.national_instruments_IDs}

    def cleanup(self) -> None:
        
        super().cleanup()

        for arduino in self.arduinos.values():
            arduino.close()
    
        for labjack in self.labjacks.values():
            labjack.close()
    
        for ni in self.nis.values():
            ni.close()

    def process_data(self, data: Dict) -> NDArray:
        '''Implementing a kind of RPC mechanism'''
        
        if data:

            result = {}

            for name, devices in [
                ('arduino', self.arduinos),
                ('labjack', self.labjacks),
                ('ni', self.nis),
            ]:

                result[name] = []
                commands = data.get(name, [])
                for board_id, operation, args in commands:
                    method = getattr(devices[board_id], operation, None)
                    if method:
                        result[name].append((board_id, operation, args, method(*args)))

            return result
        
    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        pass
        
if __name__ == '__main__':

    from dagline import ProcessingDAG
    from ipc_tools import QueueMP
    from multiprocessing_logger import Logger
    import time

    class NullNode(WorkerNode):

        def process_data(self, data):
            pass

        def process_metadata(self, metadata):
            pass

    dag = ProcessingDAG()

    worker_logger = Logger('daq_worker.txt', Logger.INFO)
    queue_logger = Logger('daq_queue.txt', Logger.INFO)

    daq_worker = DAQ_Worker(
        arduino_IDs = [board.id for board in Arduino_SoftTiming.list_boards()],
        labjack_IDs = [board.id for board in LabJackU3_SoftTiming.list_boards()],
        national_instruments_IDs = [board.id for board in NI_SoftTiming.list_boards()],
        name = 'daq',
        logger = worker_logger, 
        logger_queues = queue_logger,
    )
    source = NullNode(        
        name = 'source',
        logger = worker_logger, 
        logger_queues = queue_logger,
    )
    sink = NullNode(        
        name = 'sink',
        logger = worker_logger, 
        logger_queues = queue_logger,
    )

    input_queue = QueueMP()
    output_queue = QueueMP()

    dag.connect_data(
        sender = source, 
        receiver = daq_worker, 
        queue = input_queue, 
        name = 'daq_input'
    )

    dag.connect_data(
        sender = daq_worker, 
        receiver = sink, 
        queue = output_queue, 
        name = 'daq_output'
    )

    dag.start()
    input_queue.put(
        {
            'arduino': [
                ('/dev/ttyACM0', 'digital_write', (4, True)),
                ('/dev/ttyACM0', 'pwm_write', (9, 0.25))
            ],
            'labjack': [
                (320043003, 'digital_read', (0,)),
                (320043003, 'pwm_write', (4, 0.5)),
                (320043003, 'pwm_write', (5, 0.15))
            ]
        }
    )
    print(output_queue.get())
    time.sleep(1)

    dag.stop()
        

