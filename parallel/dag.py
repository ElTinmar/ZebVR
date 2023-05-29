import zmq
from multiprocessing import Process, Event
from typing import Any, List
from dataclasses import dataclass
from numpy.typing import DTypeLike, ArrayLike
from abc import ABC, abstractmethod

@dataclass
class DataInfo:
    shape: ArrayLike
    dtype: DTypeLike

    def __eq__(self, __value: object) -> bool:
        if __value is None:
            return False
        return (self.shape == __value.shape) and (self.dtype == __value.dtype)

class IncompatibleData(Exception):
    pass

@dataclass
class ZMQSocketInfo:
    address : str = None
    socket_type: int = None

class ZMQDataProcessingNode(ABC):
    def __init__(
            self, 
            input_info: List[DataInfo], 
            output_info: List[DataInfo]
        ) -> None:
        super().__init__()
        self.input_info = input_info
        self.output_info = output_info
        self.outsock_info = []
        self.insock_info = []
        self.input_socket = []
        self.output_socket = []
        self.process = None
        self.stop_loop = Event()

    @abstractmethod
    def pre_loop(self) -> None:
        pass

    @abstractmethod
    def post_loop(self) -> None:
        pass

    @abstractmethod
    def work(self, args: Any) -> Any:
        pass
    
    def set_outsock_info(self, outsock_info: ZMQSocketInfo) -> None:
        if outsock_info not in self.outsock_info:
            self.outsock_info.append(outsock_info)

    def set_insock_info(self, insock_info: ZMQSocketInfo) -> None:
        if insock_info not in self.insock_info:
            self.insock_info.append(insock_info)

    def configure_zmq(self):
        self.context = zmq.Context()

        for isock in self.insock_info:
            socket = self.context.socket(isock.socket_type)
            socket.connect(isock.address)
            self.input_socket.append(socket)

        for osock in self.outsock_info:
            socket = self.context.socket(osock.socket_type)
            socket.bind(osock.address)
            self.output_socket.append(socket)

    def clean_zmq(self):
        for sock in self.input_socket:
            sock.close()
        for sock in self.output_socket:
            sock.close()

    def _loop(self):
        self.configure_zmq()
        self.pre_loop()

        while not self.stop_loop.is_set():
            # receive data
            input_data = []
            for sock in self.input_socket:
                input_data.append(sock.recv_pyobj())

            # do work
            results = self.work(input_data)

            # send data
            for sock in self.output_socket:
                sock.send_pyobj(results)

        self.post_loop()
        self.clean_zmq()

    def start(self):
        # start the loop in a separate process
        self.process = Process(target = self._loop)
        self.process.start()
        
    def stop(self):
        # stop the loop
        self.stop_loop.set()
        self.process.join()

class ZMQDataProcessingEdge:
    def __init__(
            self, 
            src_node: ZMQDataProcessingNode,
            dst_node: ZMQDataProcessingNode,
            id: int,
        ) -> None:

        if src_node.output_info != dst_node.input_info:
            raise(IncompatibleData)
        
        self.src_node = src_node
        self.dst_node = dst_node
        self.id = id

        # create zmq socket info
        self.src_socket_info = ZMQSocketInfo(
            address = f'tcp://*:{id}',
            socket_type = zmq.PUSH
        )

        self.dst_socket_info = ZMQSocketInfo(
            address = f'tcp://localhost:{id}',
            socket_type = zmq.PULL
        )

        # update nodes
        self.src_node.set_outsock_info(self.src_socket_info)
        self.dst_node.set_insock_info(self.dst_socket_info)

class ZMQDataProcessingDAG:
    def __init__(self, dag_str: List[dict]):
        self.nodes = []
        self.edges = []
        for edge_dict in dag_str:
            src = edge_dict['src']
            dst = edge_dict['dst']

            edge = ZMQDataProcessingEdge(
                src_node = src,
                dst_node = dst,
                id = edge_dict['port']
            )

            if src not in self.nodes:
                self.nodes.append(src)
            if dst not in self.nodes:
                self.nodes.append(dst)
            self.edges.append(edge)

    def start(self):
        # TODO: maybe you should start from the leaves and climb up to the root
        for n in self.nodes:
            n.start()

    def stop(self):
        # TODO: maybe you should start from the root make your way to the leaves
        for n in self.nodes:
            n.stop()
