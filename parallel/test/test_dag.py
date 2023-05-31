from parallel.dag import ZMQDataProcessingDAG, ZMQDataProcessingNode
import numpy as np
import cv2
import time
from typing import Any
import zmq

class Camera(ZMQDataProcessingNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = 0

    def pre_loop(self) -> None:
        pass

    def post_loop(self) -> None:
        pass

    def post_send(self) -> None:
        pass
    
    def post_recv(self, args: Any) -> Any:
        self.counter += 1
        return [self.counter, np.random.rand(1024, 1024)]
    
class Display(ZMQDataProcessingNode):
    def __init__(self, name: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.name = name

    def pre_loop(self):
        cv2.namedWindow(self.name)

    def post_loop(self):
        cv2.destroyWindow(self.name)
    
    def post_send(self) -> None:
        pass

    def post_recv(self, data: Any) -> Any:
        # TODO socket ID depends on how you build the graph,
        # that's not ideal. Maybe use dict with names instead
        # of lists ?
        socket_id = 0
        print(f'{self.name} received frame {data[socket_id][0]}')
        cv2.imshow(self.name,data[socket_id][1])
        cv2.waitKey(1)


cam = Camera()
display_0 = Display(name = 'Display0')
display_1 = Display(name = 'Display1')

dagstr0 = [
    {
        'src': cam,
        'dst': display_0,
        'protocol': 'tcp://',
        'address' : '127.0.0.1',
        'port': 5555,
        'send_flag': zmq.NOBLOCK,
        'recv_flag': None,
        'src_binds': True
    },
    {
        'src': cam,
        'dst': display_1,
        'protocol': 'tcp://',
        'address' : '127.0.0.1',
        'port': 5555,
        'send_flag': zmq.NOBLOCK,
        'recv_flag': None,
        'src_binds': True
    }
]

dagstr1 = [
    {
        'src': cam,
        'dst': display_0,
        'protocol': 'tcp://',
        'address' : '127.0.0.1',
        'port': 5555,
        'send_flag': zmq.NOBLOCK,
        'recv_flag': None,
        'src_binds': True
    },
    {
        'src': cam,
        'dst': display_1,
        'protocol': 'tcp://',
        'address' : '127.0.0.1',
        'port': 5556,
        'send_flag': zmq.NOBLOCK,
        'recv_flag': None,
        'src_binds': True
    }
]

dagstr2 = [
    {
        'src': cam,
        'dst': display_0,
        'protocol': 'tcp://',
        'address' : '127.0.0.1',
        'port': 5555,
        'send_flag': zmq.NOBLOCK,
        'recv_flag': None,
        'src_binds': True
    }
]

dag = ZMQDataProcessingDAG(dagstr0)

dag.start()
time.sleep(10)
dag.stop()