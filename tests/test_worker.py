import time
from numpy.typing import NDArray
import numpy as np
import cv2
from typing import List, Optional

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

class Dispatcher(ZebVR_Worker):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            send_strategy=send_strategy.DISPATCH, 
            receive_strategy=receive_strategy.POLL, 
            *args, **kwargs
        )

    def work(self, data: NDArray) -> None:
        return data
    
class Collector(ZebVR_Worker):
    # NOTE this seems to not make sense

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            send_strategy=send_strategy.BROADCAST, 
            receive_strategy=receive_strategy.COLLECT, 
            *args, **kwargs
        )

    def work(self, data: List) -> None:
        return data[0] 

def test_two_senders_one_receiver():

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

    q0 = MonitoredQueue(
        RingBuffer(
            num_items = 100,
            item_shape = (HEIGHT, WIDTH),
            data_type = np.uint8
        )
    )

    q1 = MonitoredQueue(
        RingBuffer(
            num_items = 100,
            item_shape = (HEIGHT, WIDTH),
            data_type = np.uint8
        )
    )
    
    connect(sender=s0, receiver=r, queue=q0)
    connect(sender=s1, receiver=r, queue=q1)

    l.start()
    r.start()
    s0.start()
    s1.start()

    time.sleep(10)

    s0.stop()
    s1.stop()
    r.stop()
    l.stop()

    print(q0.get_average_freq())
    print(q1.get_average_freq())

def test_two_senders_one_receiver_shared_queue():

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

def test_one_sender_two_receivers():

    l = Logger('test_worker.log', Logger.DEBUG)

    s = Sender(
        name = 'Random_image_generator_0',
        logger = l,
        send_strategy = send_strategy.DISPATCH
    )

    r0 = Receiver(
        name = 'Image_displayer_0',
        logger = l,
        receive_strategy = receive_strategy.POLL
    )

    r1 = Receiver(
        name = 'Image_displayer_1',
        logger = l,
        receive_strategy = receive_strategy.POLL
    )

    q0 = MonitoredQueue(
        RingBuffer(
            num_items = 100,
            item_shape = (HEIGHT, WIDTH),
            data_type = np.uint8
        )
    )

    q1 = MonitoredQueue(
        RingBuffer(
            num_items = 100,
            item_shape = (HEIGHT, WIDTH),
            data_type = np.uint8
        )
    )
    
    connect(sender=s, receiver=r0, queue=q0)
    connect(sender=s, receiver=r1, queue=q1)

    l.start()
    r0.start()
    r1.start()
    s.start()

    time.sleep(10)

    s.stop()
    r0.stop()
    r1.stop()
    l.stop()

    print(q0.get_average_freq())
    print(q1.get_average_freq())

def test_sender_dispatcher_two_receivers():

    l = Logger('test_worker.log', Logger.DEBUG)

    s = Sender(
        name = 'Random_image_generator_0',
        logger = l,
        send_strategy = send_strategy.DISPATCH
    )

    d = Dispatcher(
        name = 'dispatcher',
        logger = l
    )

    r0 = Receiver(
        name = 'Image_displayer_0',
        logger = l,
        receive_strategy = receive_strategy.POLL
    )

    r1 = Receiver(
        name = 'Image_displayer_1',
        logger = l,
        receive_strategy = receive_strategy.POLL
    )

    q0 = MonitoredQueue(
        RingBuffer(
            num_items = 100,
            item_shape = (HEIGHT, WIDTH),
            data_type = np.uint8
        )
    )

    q1 = MonitoredQueue(
        RingBuffer(
            num_items = 100,
            item_shape = (HEIGHT, WIDTH),
            data_type = np.uint8
        )
    )

    q2 = MonitoredQueue(
        RingBuffer(
            num_items = 100,
            item_shape = (HEIGHT, WIDTH),
            data_type = np.uint8
        )
    )
    
    connect(sender=s, receiver=d, queue=q0)
    connect(sender=d, receiver=r0, queue=q1)
    connect(sender=d, receiver=r1, queue=q2)

    l.start()
    r0.start()
    r1.start()
    d.start()
    s.start()

    time.sleep(10)

    s.stop()
    d.stop()
    r0.stop()
    r1.stop()
    l.stop()

    print(q0.get_average_freq())
    print(q1.get_average_freq())
    print(q2.get_average_freq())


if __name__ == '__main__':

    #test_two_senders_one_receiver()
    test_two_senders_one_receiver_shared_queue()
    #test_one_sender_two_receivers()
    #test_sender_dispatcher_two_receivers()



