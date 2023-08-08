from multiprocessing import Process, Event
from abc import ABC
import time
from parallel.shared_ring_buffer import DataDispatcher

class DataProcessingNode(ABC):
    def __init__(
            self, 
            input: DataDispatcher,
            output: DataDispatcher,
            recv_timeout_s = 10
        ) -> None:
        super().__init__()
        self.input = input
        self.output = output
        self.process = None
        self.stop_loop = Event()
        self.recv_timeout_s = recv_timeout_s
        self.name = 'Node'

        # timing measurement
        self.recv_time_ns = 0
        self.post_recv_time_ns = 0
        self.send_time_ns = 0
        self.post_send_time_ns = 0
        self.num_loops = 0

    def pre_loop(self) -> None:
        pass

    def post_loop(self) -> None:
        print(f'{self.name}: recv {1e-9 * self.recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_recv {1e-9 * self.post_recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: send {1e-9 * self.send_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_send {1e-9 * self.post_send_time_ns/self.num_loops} s per loop')

    def post_send(self) -> None:
        pass

    def post_recv(self):
        pass

    def setup(self):
        pass

    def clean_zmq(self):
        pass

    def _loop(self, stop_loop: Event):
        self.stop_loop = stop_loop
        self.pre_loop()

        while not self.stop_loop.is_set():
            if self.input is not None:
                for inbuf in self.input:
                    start_time_ns = time.time_ns()
                    data = inbuf.unpack()
                    self.recv_time_ns += (time.time_ns() - start_time_ns)
                    results = self.post_recv(data)
                    inbuf.read_done()
                    self.post_recv_time_ns += (time.time_ns() - start_time_ns)
                    for outbuf in self.output:
                        outbuf.pack(results)
                        outbuf.write_done()
                    self.send_time_ns += (time.time_ns() - start_time_ns)
                    self.post_send()
                    self.post_send_time_ns += (time.time_ns() - start_time_ns)
                    self.num_loops += 1
            else:
                start_time_ns = time.time_ns()
                self.recv_time_ns += (time.time_ns() - start_time_ns)
                results = self.post_recv(None)
                self.post_recv_time_ns += (time.time_ns() - start_time_ns)
                for outbuf in self.output:
                        outbuf.pack(results)
                        outbuf.write_done()
                self.send_time_ns += (time.time_ns() - start_time_ns)
                self.post_send()
                self.post_send_time_ns += (time.time_ns() - start_time_ns)
                self.num_loops += 1

        self.post_loop()

    def start(self):
        # start the loop in a separate process
        self.process = Process(
            target = self._loop, 
            args = (self.stop_loop,)
        )
        self.process.start()
        
    def stop(self):
        # stop the loop
        self.stop_loop.set()
        self.process.join()
