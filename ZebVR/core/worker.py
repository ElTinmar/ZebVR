from abc import ABC, abstractmethod
from multiprocessing import Event, Process
from typing  import Any, Optional, List
import time
from itertools import cycle
from queue import Empty, Full
from enum import Enum


from multiprocessing_logger import Logger
from ipc_tools import QueueLike

class receive_strategy(Enum):
    POLL = 1
    COLLECT = 2

class send_strategy(Enum):
    BROADCAST = 1
    DISPATCH = 2

class ZebVR_Worker(ABC):

    def __init__(
            self, 
            name: str, 
            logger: Logger,
            send_block: bool = False,
            send_timeout: Optional[float] = None,
            send_strategy: send_strategy = send_strategy.BROADCAST, 
            receive_block: bool = True,
            receive_timeout: Optional[float] = 10.0,
            receive_strategy: receive_strategy = receive_strategy.POLL
        ) -> None:
        
        super().__init__()
        self.stop_event = Event()
        self.logger = logger
        self.name = name
        self.iteration = 0
        self.receive_queues = []
        self.receive_queues_iterator = None
        self.send_queues = []
        self.send_queues_iterator = None
        self.send_block = send_block
        self.send_timeout = send_timeout
        self.send_strategy = send_strategy
        self.receive_block = receive_block
        self.receive_timeout = receive_timeout
        self.receive_queues_iterator = None
        self.receive_strategy = receive_strategy

    def register_receive_queue(self, queue: QueueLike):
        self.receive_queues.append(queue)
        self.receive_queues_iterator = cycle(self.receive_queues)

    def register_send_queue(self, queue: QueueLike):
        self.send_queues.append(queue)
        self.send_queues_iterator = cycle(self.send_queues)
    
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
        if self.receive_strategy == receive_strategy.COLLECT:
            return self.collect()
        elif self.receive_strategy == receive_strategy.POLL:
            return self.poll()
        
    def collect(self) -> List:
        '''Each receive queue must receive data'''

        data = []
        for q in self.receive_queues:
            data.append(q.get(block=self.receive_block, timeout=self.receive_timeout))
        return data
    
    def poll(self) -> Optional[Any]:
        '''Return data from the first queue that is ready'''

        if self.receive_timeout is None:
            deadline = float('inf')
        else:
            deadline = time.monotonic() + self.receive_timeout

        for q in self.receive_queues_iterator:
            
            if time.monotonic() < deadline:
                return None
            
            try:
                return q.get_nowait()
            except Empty:
                pass

            # sleep a bit ?

    def send(self, data: Optional[Any]) -> None:
        '''sends data'''
        if self.send_strategy == send_strategy.BROADCAST:
            self.broadcast(data)
        elif self.send_strategy == send_strategy.DISPATCH:
            self.dispatch(data)

    def broadcast(self, data) -> None:
        '''copy data to all send queues'''

        if data is not None:
            for q in self.send_queues:            
                q.put(data, block=self.send_block, timeout=self.send_timeout)

    def dispatch(self, data) -> None:
        '''send data alternatively to each queue'''

        if self.send_timeout is None:
            deadline = float('inf')
        else:
            deadline = time.monotonic() + self.send_timeout

        for q in self.send_queues_iterator:
            
            if time.monotonic() < deadline:
                return None
            
            try:
                return q.put_nowait(data)
            except Full:
                pass

            # sleep a bit ?

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