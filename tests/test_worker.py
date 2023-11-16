import time
from numpy.typing import NDArray
import numpy as np
import cv2
from typing import List

from ZebVR import ZebVR_Worker, connect, receive_strategy, send_strategy
from ipc_tools import RingBuffer
from multiprocessing_logger import Logger

HEIGHT = 1024
WIDTH = 1024

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

    def work(self, data: List) -> None:
        cv2.imshow('receiver', data)
        cv2.waitKey(1)

if __name__ == '__main__':

    l = Logger()

    s = Sender(
        name = 'Random_image_generator',
        logger = l,
        send_strategy = send_strategy.BROADCAST
    )

    r = Receiver(
        name = 'Image_displayer',
        logger = l,
        receive_strategy = receive_strategy.POLL
    )

    q = RingBuffer(
        num_items = 100,
        item_shape = (HEIGHT, WIDTH),
        data_type = np.uint8
    ) 
    
    connect(sender=s, receiver=r, queue=q)

    r.start()
    s.start()

    time.sleep(10)

    s.stop()
    r.stop()



