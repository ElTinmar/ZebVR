from parallel.dag import *
import numpy as np
import cv2

class Camera(ZMQWorker):
    def __init__(self):
        super().__init__()
        self.counter = 0

    def pre_loop(self) -> None:
        pass

    def post_loop(self) -> None:
        pass
    
    def work(self) -> NDArray:
        self.counter += 1
        return np.random.rand(512, 512)
    
class Display(ZMQWorker):
    def pre_loop(self):
        cv2.namedWindow('Display')

    def post_loop(self):
        cv2.destroyWindow('Display')

    def work(self, data: NDArray) -> None:
        cv2.imshow('Display',data)
        cv2.waitKey(1)

cam = Camera()
display = Display()

dagstr = [
    (cam,display,5555,(512,512),np.single),
    (cam,display,5555,(512,512),np.single)
]

src = ZMQDataProcessingNode(
    input_info = None,
    output_info = DataInfo(
        shape = (512,512),
        dtype = np.single
    ),
    worker = cam
)

display_0 = ZMQDataProcessingNode(
    input_info = DataInfo(
        shape = (512,512),
        dtype = np.single
    ),
    output_info = None,
    worker = display
)

display_1 = ZMQDataProcessingNode(
    input_info = DataInfo(
        shape = (512,512),
        dtype = np.single
    ),
    output_info = None,
    worker = display
)

edge_0 = ZMQDataProcessingEdge(
    src_node=src,
    dst_node=display_0,
    id = 5555
)

edge_1 = ZMQDataProcessingEdge(
    src_node=src,
    dst_node=display_1,
    id = 5555
)

dag = DataProcessingDAG(
    nodes = [src, display_0, display_1],
    edges = [edge_0, edge_1]
)

dag.start()
