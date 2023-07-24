from parallel.shared_ring_buffer import SharedRingBuffer, BufferCollection
import multiprocessing as mp
import numpy as np
import cv2
from typing import List
import time

SIZE = (1024, 1024, 3)
NLOOP = 1000

def monitor(buffers: List[SharedRingBuffer]):
    while True:
        for idx, buf in enumerate(buffers):
            print(f'{idx}: {buf.size()}', flush=True)
        time.sleep(0.1)

def consumer(input: BufferCollection):
    cv2.namedWindow('display')
    for i in range(NLOOP):
        buffer = input.read()
        if buffer is not None:
            empty, data = buffer.get_read_buffer()
            array = np.frombuffer(data, dtype='B').reshape(SIZE)
            cv2.imshow('display',array)
            cv2.waitKey(1)
            buffer.read_done()
    cv2.destroyWindow('display')

def producer(output: BufferCollection, val: int):
    for i in range(NLOOP//2):
        buffer = output.write()[0]
        full, data = buffer.get_write_buffer()
        data[:] = np.random.randint(0, 255, (np.prod(SIZE),), dtype='B')//val
        buffer.write_done()
    
if __name__ == '__main__':
    mp.set_start_method('spawn')

    ringbuf1 = SharedRingBuffer(num_element=NLOOP//2, element_byte_size=int(np.prod(SIZE)))
    ringbuf2 = SharedRingBuffer(num_element=NLOOP//2, element_byte_size=int(np.prod(SIZE)))
    
    collection1 = BufferCollection([ringbuf1,ringbuf2], dispatch=True)
    collection2 = BufferCollection([ringbuf2])
    collection3 = BufferCollection([ringbuf1, ringbuf2])

    pcons = mp.Process(target=consumer, args=(collection3,))
    pprod1 = mp.Process(target=producer, args=(collection1, 2))
    pprod2 = mp.Process(target=producer, args=(collection2, 1))
    pmon = mp.Process(target=monitor, args=([ringbuf1, ringbuf2],))

    pmon.start()
    pcons.start()
    pprod1.start()
    pprod2.start()

    pprod1.join()
    pprod2.join()
    pcons.join()
    pmon.terminate()

