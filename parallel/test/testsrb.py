from parallel.shared_ring_buffer import SharedRingBuffer, DataManager, DataDispatcher
import multiprocessing as mp
import numpy as np
import cv2
from typing import List
import time
import sys

SIZE = (1024, 1024, 3)
HEADER_SIZE = 22
NLOOP = 1000
BUFSIZE = 20

'''
Frame message structure:
- sentinel (1 byte)
- frame_num (4 bytes)
- timestamp (8 bytes)
- image height (4 bytes)
- image width (4 bytes)
- num image channels (1 bytes)
- pixel data (h*w*c bytes)
'''

def pack_frame_and_metadata(
        buffer,
        sentinel,
        frame_num,
        timestamp,
        height,
        width,
        channels,
        pixel_data
    ) -> None:

    buffer[:1] = memoryview(sentinel.to_bytes(1,sys.byteorder))
    buffer[1:5] = memoryview(frame_num.to_bytes(4,sys.byteorder))
    buffer[5:13] = memoryview(timestamp.to_bytes(8,sys.byteorder))
    buffer[13:17] = memoryview(height.to_bytes(4,sys.byteorder))
    buffer[17:21] = memoryview(width.to_bytes(4,sys.byteorder))
    buffer[21:22] = memoryview(channels.to_bytes(1,sys.byteorder))
    buffer[22:] = pixel_data

def unpack_frame_and_metadata(buffer):

    sentinel = int.from_bytes(buffer[:1], sys.byteorder)
    frame_num = int.from_bytes(buffer[1:5], sys.byteorder)
    timestamp = int.from_bytes(buffer[5:13], sys.byteorder)
    height = int.from_bytes(buffer[13:17], sys.byteorder)
    width = int.from_bytes(buffer[17:21], sys.byteorder)
    channels = int.from_bytes(buffer[21:22], sys.byteorder)
    pixel_data = buffer[22:]
    return (sentinel, frame_num, timestamp, height, width, channels, pixel_data)

def monitor(buffers: List[SharedRingBuffer]):
    while True:
        for idx, buf in enumerate(buffers):
            print(f'{idx}: {buf.size()}', flush=True)
        time.sleep(0.1)

def consumer(input: DataDispatcher):
    cv2.namedWindow('display')
    while True:
        manager = input.read()
        if manager is not None:
            (sentinel, frame_num, timestamp, height, width, channels, pixel_data) = manager.unpack()
            print(f'received (#{frame_num}: {timestamp}), ({height}, {width}, {channels}), sentinel {sentinel}' , flush=True)
            cv2.imshow('display', pixel_data.reshape(SIZE))
            cv2.waitKey(1)
            manager.read_done()
            if sentinel > 0:
                break
    cv2.destroyWindow('display')

def producer(output: DataDispatcher, val: int):
    frame_num = 0
    sentinel = 0
    height = SIZE[0]
    width = SIZE[1]
    channels = SIZE[2]
    for i in range(NLOOP//2):
        if i == NLOOP//2-1:
            sentinel = 1
        frame_num += 1
        timestamp = time.time_ns()
        pixel_data = np.random.randint(0, 255, (np.prod(SIZE),), dtype='B')//val

        for manager in output.write():
            manager.pack(
                sentinel,
                frame_num,
                timestamp,
                height,
                width,
                channels,
                pixel_data
            )
            manager.write_done()
    
if __name__ == '__main__':
    mp.set_start_method('spawn')

    ringbuf1 = SharedRingBuffer(num_element=BUFSIZE, element_size=HEADER_SIZE+int(np.prod(SIZE)))
    ringbuf2 = SharedRingBuffer(num_element=BUFSIZE, element_size=HEADER_SIZE+int(np.prod(SIZE)))
    
    manager1 = DataManager(
        buffer = ringbuf1, 
        packer = pack_frame_and_metadata, 
        unpacker = unpack_frame_and_metadata
    )
    manager2 = DataManager(
        buffer = ringbuf2, 
        packer = pack_frame_and_metadata, 
        unpacker = unpack_frame_and_metadata
    )

    dispatcher1 = DataDispatcher([manager1])
    dispatcher2 = DataDispatcher([manager2])
    dispatcher3 = DataDispatcher([manager1, manager2])

    pcons = mp.Process(target=consumer, args=(dispatcher3,))
    pprod1 = mp.Process(target=producer, args=(dispatcher1, 2))
    pprod2 = mp.Process(target=producer, args=(dispatcher2, 1))
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

