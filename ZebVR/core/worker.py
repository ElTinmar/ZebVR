from abc import ABC, abstractmethod
from multiprocessing import Event, Process
from typing  import Any, Optional
import time

from multiprocessing_logger import Logger
from ipc_tools import QueueLike

class ZebVR_Worker(ABC):

    def __init__(
            self, 
            name: str, 
            logger: Logger,
            send_block: bool = False,
            receive_block: bool = True,
            send_timeout: Optional[float] = None,
            receive_timeout: Optional[float] = 10.0
        ) -> None:
        
        super().__init__()
        self.stop_event = Event()
        self.logger = logger
        self.name = name
        self.iteration = 0
        self.receive_queues = []
        self.send_queues = []
        self.send_block = send_block
        self.receive_block = receive_block
        self.send_timeout = send_timeout
        self.receive_timeout = receive_timeout

    def register_receive_queue(self, queue: QueueLike):
        self.receive_queues.append(queue)

    def register_send_queue(self, queue: QueueLike):
        self.send_queues.append(queue)
    
    def main_loop(self):

        self.initialize()

        while not self.stop_event.is_set():
            t0_ns = time.monotonic_ns()
            data = self.receive()
            t1_ns = time.monotonic_ns() 
            results = self.work(data)
            t2_ns = time.monotonic_ns()
            self.send(results)
            t3_ns = time.monotonic_ns()
            self.iteration += 1
            self.log_timings(self.iteration, t0_ns,t1_ns,t2_ns,t3_ns)
            
        self.cleanup()

    def log_timings(self, iteration: int, t0_ns: int, t1_ns: int, t2_ns: int, t3_ns: int):
        
        receive_time_ms = (t1_ns - t0_ns) * 1e-6
        process_time_ms = (t2_ns - t1_ns) * 1e-6
        send_time_ms = (t3_ns - t2_ns) * 1e-6

        self.local_logger.debug(f'''
            #{iteration} ,
            receive_time: {receive_time_ms}, 
            process_time: {process_time_ms}, 
            send_time: {send_time_ms}
        ''')

    def initialize(self) -> None:
        '''initialize resources at the beginning of the loop in a new process'''
        self.logger.configure_emitter()
        self.local_logger = self.logger.get_logger(self.name)

    def cleanup(self) -> None:
        '''cleans resources at the end'''

    def receive(self) -> Optional[Any]:
        '''receive data'''
        data = []
        for q in self.receive_queues:
            data.append(q.get(block=self.receive_block, timeout=self.receive_timeout))
        return data
    
    def send(self, data: Optional[Any]) -> None:
        '''sends data'''
        if data is not None:
            for q in self.send_queues:            
                q.put(data, block=self.send_block, timeout=self.send_timeout)

    @abstractmethod
    def work(self, data: Any) -> Any:
        '''does the actual processing'''
        
    def start(self):
        '''start the loop in a separate process'''
        self.process = Process(target = self.main_loop)
        self.process.start()
        
    def stop(self):
        '''stop the loop and join process'''
        self.stop_event.set()
        self.process.join()

def connect(sender: ZebVR_Worker, receiver: ZebVR_Worker, queue: QueueLike):
    sender.register_send_queue(queue)
    receiver.register_receive_queue(queue)