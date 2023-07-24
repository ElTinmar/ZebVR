import zmq
from multiprocessing import Process, Event
from typing import Any, List, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import time

# TODO use shared ring buffers to share information

@dataclass
class ZMQSocketInfo:
    address : str = "127.0.0.1"
    port: int = 5555
    protocol: str = 'tcp://'
    socket_type: int = None
    flag: int = 0
    copy: bool = True
    track: bool = False
    bind: bool = False
    serializer: Callable = None
    deserializer: Callable = None

class ZMQDataProcessingNode(ABC):
    def __init__(
            self, 
            input_info: List[ZMQSocketInfo],
            output_info: List[ZMQSocketInfo],
            recv_timeout_s = 10
        ) -> None:
        super().__init__()
        self.outsock_info = output_info
        self.insock_info = input_info
        self.input_socket = []
        self.output_socket = []
        self.process = None
        self.poller = None
        self.stop_loop = Event()
        self.recv_timeout_s = recv_timeout_s
        self.name = 'ZMQNode'

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

    def post_recv(self, args: Any) -> Any:
        pass

    def configure_zmq(self):
        self.context = zmq.Context()
        self.context.setsockopt(zmq.RCVTIMEO, self.recv_timeout_s*1000)
        self.poller = zmq.Poller()

        for isock in self.insock_info:
            socket = self.context.socket(isock.socket_type)
            endpoint = isock.protocol + isock.address + f':{isock.port}'
            if isock.bind:
                socket.bind(endpoint)
            else:
                socket.connect(endpoint)
            self.input_socket.append(socket)
            self.poller.register(socket, zmq.POLLIN)

        for osock in self.outsock_info:
            socket = self.context.socket(osock.socket_type)
            endpoint = osock.protocol + osock.address + f':{osock.port}'
            if osock.bind:
                socket.bind(endpoint)
            else:
                socket.connect(endpoint)
            self.output_socket.append(socket)

    def clean_zmq(self):
        for sock in self.input_socket:
            sock.close()
        for sock in self.output_socket:
            sock.close()
        self.context.destroy()

    def _receive(self, socket: zmq.Socket, info: ZMQSocketInfo) -> Any:
        if info.deserializer is not None:
            input_data = info.deserializer(
                socket, 
                flags = info.flag,
                copy = info.copy,
                track = info.track
            )
        else:
            input_data = socket.recv_pyobj(flags = info.flag)
        return input_data
    
    def _send(self, socket: zmq.Socket, info: ZMQSocketInfo, data: Any) -> None:
        try:
            if info.serializer is not None:
                info.serializer(
                    socket, 
                    data,
                    flags = info.flag,
                    copy = info.copy,
                    track = info.track
                )
            else:
                socket.send_pyobj(
                    data, 
                    flags = info.flag
                )
        except zmq.ZMQError:
            print('Send queue is full, message was discarded')

    def _loop(self, stop_loop: Event):
        self.stop_loop = stop_loop
        self.configure_zmq()
        self.pre_loop()

        while not self.stop_loop.is_set():
            try:
                if self.input_socket:
                    events = dict(self.poller.poll(self.recv_timeout_s*1000))
                    if not events:
                        raise(zmq.error.Again)
                    for sock, info in zip(self.input_socket,self.insock_info):
                        if sock in events and events[sock] == zmq.POLLIN:
                            start_time_ns = time.time_ns()
                            data = self._receive(sock, info)
                            self.recv_time_ns += (time.time_ns() - start_time_ns)
                            results = self.post_recv(data)
                            self.post_recv_time_ns += (time.time_ns() - start_time_ns)
                            for sock, info in zip(self.output_socket, self.outsock_info):
                                self._send(sock, info, results)
                            self.send_time_ns += (time.time_ns() - start_time_ns)
                            self.post_send()
                            self.post_send_time_ns += (time.time_ns() - start_time_ns)
                            self.num_loops += 1
                else:
                    start_time_ns = time.time_ns()
                    self.recv_time_ns += (time.time_ns() - start_time_ns)
                    results = self.post_recv(None)
                    self.post_recv_time_ns += (time.time_ns() - start_time_ns)
                    for sock, info in zip(self.output_socket, self.outsock_info):
                        self._send(sock, info, results)
                    self.send_time_ns += (time.time_ns() - start_time_ns)
                    self.post_send()
                    self.post_send_time_ns += (time.time_ns() - start_time_ns)
                    self.num_loops += 1
            except zmq.error.Again:
                print('timeout, shutting down.')
                break

        self.post_loop()
        self.clean_zmq()

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
