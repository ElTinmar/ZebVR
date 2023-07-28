from parallel.shared_ring_buffer import SharedRingBuffer, BufferCollection
import multiprocessing as mp
import numpy as np
import cv2
from typing import List
import time
import struct

SIZE = (1024, 1024, 3)
NLOOP = 1000

def monitor(buffers: List[SharedRingBuffer]):
    while True:
        for idx, buf in enumerate(buffers):
            print(f'{idx}: {buf.size()}', flush=True)
        time.sleep(0.1)

def consumer(input: BufferCollection):
    cv2.namedWindow('display')
    while True:
        buffer = input.read()
        if buffer is not None:
            empty, data = buffer.get_read_buffer()
            sentinel = data[0]
            frame_num = 2**24 * data[1] + 2**16 * data[2] + 2**8 * data[3] + data[4]
            print(f'received {frame_num}, sentinel {sentinel}', flush=True)
            frame = data[5:]
            cv2.imshow('display',frame.reshape(SIZE))
            cv2.waitKey(1)
            buffer.read_done()
            if sentinel > 0:
                break
    cv2.destroyWindow('display')

def producer(output: BufferCollection, val: int):
    frame_num = 0
    sentinel = 0
    for i in range(NLOOP//2):
        buffer = output.write()[0]
        full, data = buffer.get_write_buffer()
        frame_num += 1
        if i == NLOOP//2-1:
            sentinel = 1
        frame = np.random.randint(0, 255, (np.prod(SIZE),), dtype='B')//val
        payload = np.hstack(
            (sentinel,
            struct.unpack('BBBB',frame_num.to_bytes(4,'big')),
            frame))
        data[:] = payload 
        buffer.write_done()
    
if __name__ == '__main__':
    mp.set_start_method('spawn')

    # data structure:
    # sentinel: 1 byte 
    # frame number: 4 bytes 
    # frame data: height*width*channel*bitdepth bytes 

    ringbuf1 = SharedRingBuffer(num_element=500, element_size=5+int(np.prod(SIZE)))
    ringbuf2 = SharedRingBuffer(num_element=500, element_size=5+int(np.prod(SIZE)))
    
    collection1 = BufferCollection([ringbuf1])
    collection2 = BufferCollection([ringbuf2])
    collection3 = BufferCollection([ringbuf1, ringbuf2])

    pcons = mp.Process(target=consumer, args=(collection3,))
    pprod1 = mp.Process(target=producer, args=(collection1, 2))
    pprod2 = mp.Process(target=producer, args=(collection2, 1))
    pmon = mp.Process(target=monitor, args=([ringbuf1, ringbuf2],))

    start_time = time.time()
    pmon.start()
    pcons.start()
    pprod1.start()
    pprod2.start()

    pprod1.join()
    pprod2.join()
    pcons.join()
    pmon.terminate()
    elapsed_time = time.time() - start_time
    print(f'time {elapsed_time}')

