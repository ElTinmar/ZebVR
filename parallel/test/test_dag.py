from parallel.dag import *
import numpy as np
import cv2
import time
from numpy.typing import NDArray, ArrayLike

class Camera(ZMQDataProcessingNode):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = 0

    def pre_loop(self) -> None:
        pass

    def post_loop(self) -> None:
        pass
    
    def work(self, args: Any) -> Any:
        self.counter += 1
        return [self.counter, np.random.rand(512, 512)]
    
class Display(ZMQDataProcessingNode):
    def __init__(self, name: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.name = name

    def pre_loop(self):
        cv2.namedWindow(self.name)

    def post_loop(self):
        cv2.destroyWindow(self.name)

    def work(self, data: Any) -> Any:
        socket_id = 0
        print(f'{self.name} received frame {data[socket_id][0]}')
        cv2.imshow(self.name,data[socket_id][1])
        cv2.waitKey(1)

frame_info = DataInfo(
    shape=(512,512),
    dtype=np.single
)
timestamp_info = DataInfo(
        shape=(1,),
        dtype=np.int64
)
cam = Camera(
    input_info = None, 
    output_info = [timestamp_info, frame_info]
)
display_0 = Display(
    name = 'Display0',
    input_info = [timestamp_info, frame_info], 
    output_info = None
)
display_1 = Display(
    name = 'Display1',
    input_info = [timestamp_info, frame_info], 
    output_info = None
)

# TODO parse this JSON representation of the DAG
# to build the graph automatically
dagstr = [
    {
        'src': cam,
        'dst': display_0,
        'port': 5555
    },
    {
        'src': cam,
        'dst': display_1,
        'port': 5555
    }
]

dag = ZMQDataProcessingDAG(dagstr)

dag.start()
time.sleep(10)
dag.stop()