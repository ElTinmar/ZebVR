import zmq
from multiprocessing import Process, Event
from typing import Any, List
from dataclasses import dataclass
from numpy.typing import DTypeLike, ArrayLike
from abc import ABC, abstractmethod

@dataclass
class ZMQSocketInfo:
    address : str = None
    socket_type: int = None
    flag: int = None

class ZMQDataProcessingNode(ABC):
    def __init__(
            self, 
            recv_timeout_s = 1
        ) -> None:
        super().__init__()
        self.outsock_info = []
        self.insock_info = []
        self.input_socket = []
        self.output_socket = []
        self.process = None
        self.stop_loop = Event()
        self.recv_timeout_s = recv_timeout_s

    @abstractmethod
    def pre_loop(self) -> None:
        pass

    @abstractmethod
    def post_loop(self) -> None:
        pass

    @abstractmethod
    def post_send(self) -> None:
        pass

    @abstractmethod
    def post_recv(self, args: Any) -> Any:
        pass
    
    def set_outsock_info(self, outsock_info: ZMQSocketInfo) -> None:
        if outsock_info not in self.outsock_info:
            self.outsock_info.append(outsock_info)

    def set_insock_info(self, insock_info: ZMQSocketInfo) -> None:
        if insock_info not in self.insock_info:
            self.insock_info.append(insock_info)

    def configure_zmq(self):
        self.context = zmq.Context()
        self.context.setsockopt(zmq.RCVTIMEO,self.recv_timeout_s*1000)

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
        self.context.destroy()

    def _loop(self):
        self.configure_zmq()
        self.pre_loop()

        while not self.stop_loop.is_set():
            # receive data
            input_data = []
            try:
                for sock, info in zip(self.input_socket,self.insock_info):
                    if info.flag is not None:
                        input_data.append(sock.recv_pyobj(flags = info.flag))
                    else:
                        input_data.append(sock.recv_pyobj())
            except zmq.error.Again:
                print('receive timeout, shutting down')
                break

            # do post_recv
            results = self.post_recv(input_data)

            # send data
            try:
                for sock, info in zip(self.output_socket, self.outsock_info):
                    if info.flag is not None:
                        sock.send_pyobj(results, flags = info.flag)
                    else:
                        sock.send_pyobj(results)
            except zmq.ZMQError:
                print('Send queue is full, message was discarded')
                

            self.post_send()

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
            port: int,
            send_flag: int = None,
            recv_flag: int = None
        ) -> None:
        
        self.src_node = src_node
        self.dst_node = dst_node
        self.port = port
        self.send_flag = send_flag
        self.recv_flag = recv_flag

        # create zmq socket info
        self.src_socket_info = ZMQSocketInfo(
            address = f'tcp://*:{port}',
            socket_type = zmq.PUSH,
            flag = send_flag
        )

        self.dst_socket_info = ZMQSocketInfo(
            address = f'tcp://localhost:{port}',
            socket_type = zmq.PULL,
            flag = recv_flag
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
                port = edge_dict['port'],
                send_flag = edge_dict['send_flag'],
                recv_flag = edge_dict['recv_flag'],
            )

            # NOTE There is some black magic going on here,
            # maybe make that more explicit ?
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
        # TODO: maybe you should start from the root and make your way to the leaves
        for n in self.nodes:
            n.stop()
