import time
from numpy.typing import NDArray
import numpy as np
import cv2
from typing import List

from ZebVR import ZebVR_Worker, connect, receive_strategy, send_strategy
from ipc_tools import RingBuffer, QueueMP, ZMQ_PushPullArray, MonitoredQueue
from multiprocessing_logger import Logger

HEIGHT = 2048
WIDTH = 2048

class Sender(ZebVR_Worker):

    def work(self, data: None) -> NDArray:
        return np.random.randint(0,255,(HEIGHT,WIDTH), dtype=np.uint8)

class Receiver(ZebVR_Worker):

    def initialize(self) -> None:
        super().initialize()
        cv2.namedWindow('receiver')
    
    def cleanup(self) -> None:
        super().cleanup()
        cv2.destroyAllWindows()

    def work(self, data: NDArray) -> None:
        cv2.imshow('receiver', data)
        cv2.waitKey(1)

if __name__ == '__main__':

    l = Logger('test_worker.log', Logger.DEBUG)

    s0 = Sender(
        name = 'Random_image_generator_0',
        logger = l,
        send_strategy = send_strategy.BROADCAST
    )

    s1 = Sender(
        name = 'Random_image_generator_1',
        logger = l,
        send_strategy = send_strategy.BROADCAST
    )

    r = Receiver(
        name = 'Image_displayer',
        logger = l,
        receive_strategy = receive_strategy.POLL
    )

    q = MonitoredQueue(
        RingBuffer(
            num_items = 100,
            item_shape = (HEIGHT, WIDTH),
            data_type = np.uint8
        )
    )

    #q = MonitoredQueue(QueueMP()) 
    
    connect(sender=s0, receiver=r, queue=q)
    connect(sender=s1, receiver=r, queue=q)

    l.start()
    r.start()
    s0.start()
    s1.start()

    time.sleep(10)

    s0.stop()
    s1.stop()
    r.stop()
    l.stop()

    print(q.get_average_freq())


