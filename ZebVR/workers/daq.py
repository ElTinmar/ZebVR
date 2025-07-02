from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional, List, Union
from daq_tools import Arduino_SoftTiming, LabJackU3_SoftTiming, NI_SoftTiming

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

        self.arduinos = {board_id: Arduino_SoftTiming(board_id) for board_id in self.arduino_IDs}
        self.labjacks = {board_id: LabJackU3_SoftTiming(board_id) for board_id in self.labjack_IDs}
        self.nis = {board_id: NI_SoftTiming(board_id) for board_id in self.national_instruments_IDs}
        
        super().initialize()

    def cleanup(self) -> None:
        
        for arduino in self.arduinos.values():
            arduino.close()
    
        for labjack in self.labjacks.values():
            labjack.close()
    
        for ni in self.nis.values():
            ni.close()

        super().cleanup()

    def process_data(self, data: Dict) -> NDArray:
        pass
        
    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        '''Implementing a kind of RPC mechanism'''
        
        #control = metadata['daq_input']
        control = metadata
        
        if control:

            result = {}

            for name, devices in [
                ('arduino', self.arduinos),
                ('labjack', self.labjacks),
                ('ni', self.nis),
            ]:

                result[name] = []
                commands = control.get(name, [])
                for board_id, operation, args in commands:
                    method = getattr(devices[board_id], operation, None)
                    if method:
                        result[name].append((board_id, operation, args, method(*args)))

            return result


if __name__ == '__main__':

    from dagline import ProcessingDAG, EmptyNode, send_strategy, receive_strategy
    from ipc_tools import QueueMP
    from multiprocessing_logger import Logger
    import time
    from multiprocessing import Process, set_start_method

    set_start_method('spawn')

    worker_logger = Logger('daq_worker.txt', Logger.INFO)
    queue_logger = Logger('daq_queue.txt', Logger.INFO)
    
    # create worker nodes
    source = EmptyNode(        
        name = 'source',
        logger = worker_logger, 
        logger_queues = queue_logger,
        send_metadata_strategy = send_strategy.BROADCAST,
    )
    daq_worker = DAQ_Worker(
        arduino_IDs = [board.id for board in Arduino_SoftTiming.list_boards()],
        labjack_IDs = [board.id for board in LabJackU3_SoftTiming.list_boards()],
        national_instruments_IDs = [board.id for board in NI_SoftTiming.list_boards()],
        name = 'daq',
        logger = worker_logger, 
        logger_queues = queue_logger,
        send_metadata_strategy = send_strategy.DISPATCH,
        receive_metadata_strategy = receive_strategy.POLL,
    )
    sink = EmptyNode(        
        name = 'sink',
        logger = worker_logger, 
        logger_queues = queue_logger,
        receive_metadata_strategy = receive_strategy.POLL,
    )

    # create queues
    input_queue = QueueMP()
    output_queue = QueueMP()

    # create DAG
    dag = ProcessingDAG()
    dag.connect_metadata(
        sender = source, 
        receiver = daq_worker, 
        queue = input_queue, 
        name = 'daq_input'
    )
    dag.connect_metadata(
        sender = daq_worker, 
        receiver = sink, 
        queue = output_queue, 
        name = 'daq_output'
    )

    # start DAG
    p_worker_logger = Process(target=worker_logger.run)
    p_queue_logger = Process(target=queue_logger.run)
    p_worker_logger.start()
    p_queue_logger.start()
    dag.start()

    # highjack queues for testing
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
            ],
            #'ni': [
            #    (0, 'digital_write', (0, True))
            #]
        }
    )
    print(output_queue.get()) 
    time.sleep(1)
    print(output_queue.qsize())
    print(input_queue.qsize())

    # stop DAG
    dag.stop()
    worker_logger.stop()
    queue_logger.stop()
    p_worker_logger.join()
    p_queue_logger.join()


