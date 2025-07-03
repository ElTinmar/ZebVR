from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional, List, Union
from daq_tools import (
    Arduino_SoftTiming, 
    LabJackU3_SoftTiming, 
    NI_SoftTiming, 
    BoardInfo, 
    BoardType,
    board_type_constructors
)

class DAQ_Worker(WorkerNode):

    def __init__(
            self, 
            daq_boards: List[BoardInfo],
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.daq_boards = daq_boards

    def initialize(self) -> None:

        self.daqs = {}
        for board in self.daq_boards:
            if board.board_type not in self.daqs:
                self.daqs[board.board_type] = {
                    board.id: board_type_constructors[board.board_type](board.id)
                }
            else:
                self.daqs[board.board_type].update({
                    board.id: board_type_constructors[board.board_type](board.id)
                }) 

        print(self.daqs)

        super().initialize()

    def cleanup(self) -> None:
        
        for board_type in self.daqs.values():
            for board in board_type.values():
                board.close()

        super().cleanup()

    def process_data(self, data: Dict) -> NDArray:
        pass
        
    def process_metadata(self, metadata: Dict) -> Optional[List]:
        '''Implementing a kind of RPC mechanism'''
        
        #control = metadata['daq_input']
        control = metadata
        
        if control:

            result = []

            for board_type, board_id, operation, args, kwargs in control:
                try:
                    method = getattr(self.daqs[board_type][board_id], operation, None)
                    if method:
                        result.append((board_type, board_id, operation, args, kwargs, method(*args, **kwargs)))
                except KeyError:
                    # TODO log something?
                    return
                
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

    daq_boards = Arduino_SoftTiming.list_boards() + LabJackU3_SoftTiming.list_boards() + NI_SoftTiming.list_boards()
    source = EmptyNode(        
        name = 'source',
        logger = worker_logger, 
        logger_queues = queue_logger,
        send_metadata_strategy = send_strategy.BROADCAST,
    )
    daq_worker = DAQ_Worker(
        daq_boards = daq_boards,
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
    input_queue.put([
        (BoardType.ARDUINO, '/dev/ttyACM0', 'digital_write', (4, True), {}),
        (BoardType.ARDUINO, '/dev/ttyACM0', 'pwm_pulse', (9,), {'duration': 3, 'duty_cycle': 0.25, 'blocking': False}),
        (BoardType.LABJACK, 320043003, 'digital_read', (0,), {}),
        (BoardType.LABJACK, 320043003, 'pwm_write', (4, 0.5), {}),
        (BoardType.LABJACK, 320043003, 'pwm_write', (5, 0.15), {}),
        (BoardType.NATIONAL_INSTRUMENTS, 0, 'digital_write', (0, True), {})
    ])
       
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


