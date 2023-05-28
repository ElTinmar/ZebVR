import zmq
from multiprocessing import Process
from typing import Any, List
from dataclasses import dataclass
from numpy.typing import NDArray, DTypeLike
from abc import ABC, abstractmethod

@dataclass
class DataInfo:
    shape: NDArray
    dtype: DTypeLike

    def __eq__(self, __value: object) -> bool:
        return (self.shape == __value.shape) and (self.dtype == __value.dtype)

class IncompatibleData(Exception):
    pass

@dataclass
class ZMQSocketInfo:
    address : str = None
    socket_type: int = None

class ZMQWorker(ABC):
    def __init__(self) -> None:
        super().__init__()
        self.outsock_info = None
        self.insock_info = None
        self.process = None
        self.keepgoing = False

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
        self.outsock_info = outsock_info

    def set_insock_info(self, insock_info: ZMQSocketInfo) -> None:
        self.insock_info = insock_info

    def configure_zmq(self):
        self.context = zmq.Context()
        if self.insock_info is not None:
            self.input_socket = self.context.socket(self.insock_info.socket_type)
            self.input_socket.connect(self.insock_info.address)
        else:
            self.input_socket = None

        if self.outsock_info is not None:
            self.output_socket = self.context.socket(self.outsock_info.socket_type)
            self.output_socket.bind(self.outsock_info.address)
        else:
            self.output_socket = None

    def clean_zmq(self):
        if self.input_socket is not None:
            self.input_socket.close()
        if self.output_socket is not None:
            self.output_socket.close()

    def _loop(self):
        self.configure_zmq()
        self.pre_loop()

        while self.keepgoing:
            # receive data
            if self.input_socket is not None:
                input_data = self.input_socket.recv_pyobj()

                # do work
                results = self.work(input_data)

            else:
                results = self.work()

            # send data
            if self.output_socket is not None:
                if results is not None:
                    self.output_socket.send_pyobj(results)

        self.post_loop()
        self.clean_zmq()

    def start(self):
        # start the loop in a separate process
        self.keepgoing = True
        self.process = Process(target = self._loop)
        self.process.start()
        
    def stop(self):
        # stop the loop
        self.keepgoing = False
        self.process.join()

@dataclass
class ZMQDataProcessingNode:
    input_info: DataInfo
    output_info: DataInfo
    worker: ZMQWorker

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

        # update ZMQWorkers
        self.src_node.worker.set_outsock_info(self.src_socket_info)
        self.dst_node.worker.set_insock_info(self.dst_socket_info)

class DataProcessingDAG:
    def __init__(
            self, 
            nodes: List[ZMQDataProcessingNode], 
            edges: List[ZMQDataProcessingEdge]
        ) -> None:
        self.nodes = nodes
        self.edges = edges

    def start(self):
        # TODO: maybe you should start from the leaves and climb up to the root
        for n in self.nodes:
            n.worker.start()

    def stop(self):
        # TODO: maybe you should start from the root make your way to the leaves
        for n in self.nodes:
            n.worker.stop()
