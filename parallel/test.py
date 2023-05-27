import zmq
from multiprocessing import Process
from typing import Protocol, Any
from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray
import cv2
import time

@dataclass
class SocketInfo:
    address : str = None
    socket_type: int = None

class Worker(Protocol):
    def work(*args, **kwargs) -> Any:
        ...

class Test:

    def __init__(
        self, 
        input_info: SocketInfo, 
        output_info: SocketInfo, 
        worker: Worker
    ) -> None:
        
        self.input_info = input_info
        self.output_info = output_info
        self.worker = worker
        self.keepgoing = None
        self.process = None

    def configure_zmq(self):

        self.context = zmq.Context()

        if self.input_info is not None:
            self.input_socket = self.context.socket(self.input_info.socket_type)
            self.input_socket.connect(self.input_info.address)
        else:
            self.input_socket = None

        if self.output_info is not None:
            self.output_socket = self.context.socket(self.output_info.socket_type)
            self.output_socket.bind(self.output_info.address)
        else:
            self.output_socket = None

    def clean_zmq(self):

        if self.input_socket is not None:
            self.input_socket.close()

        if self.output_socket is not None:
            self.output_socket.close()

    def _loop(self):
        print('loop started')

        self.configure_zmq()

        while self.keepgoing:
            # receive data
            if self.input_socket is not None:
                input_data = self.input_socket.recv_pyobj()

                # do work
                results = self.worker.work(input_data)
            else:
                results = self.worker.work()

            # send data
            if self.input_socket is not None:
                self.output_socket.send_pyobj(results)

        print('loop over')
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

if __name__ == '__main__':

    class Cam(Worker):
        def work(self) -> NDArray:
            return np.random.rand(100,100)

    class Display(Worker):
        def __init__(self) -> None:
            super().__init__()
            cv2.namedWindow('Display')

        def work(self, image: NDArray) -> None:
            cv2.imshow(image)
            cv2.waitKey(1)
             
    cam = Cam()
    disp = Display() 
    cam_out = SocketInfo(address="tcp://*:5555", socket_type=zmq.PUSH)
    display_in = SocketInfo(address="tcp://localhost:5555", socket_type=zmq.PULL)

    t0 = Test(input_info=None, output_info=cam_out,worker=cam)
    t1 = Test(input_info=display_in, output_info=None, worker=disp)

    t1.start()
    t0.start()

    time.sleep(10)

    t0.stop()
    t1.stop()
