import numpy as np
from parallel.shared_ring_buffer import SharedRingBuffer
from multiprocessing import Process
import multiprocessing as mp
import time

BIG_ARRAY = np.random.randint(0,255,(4096,4096), dtype='B')
NLOOP = 100

def consumer(buffer: SharedRingBuffer, nloop):
    # start timing
    start_time = time.time_ns()

    for i in range(nloop):
        buffer.data_available.wait()
        _, buf = buffer.get_read_buffer()
        array = np.frombuffer(buf, dtype='B')
        print(np.mean(array))
        buffer.read_done()

    # stop timing
    stop_time = time.time_ns() - start_time
    print(f'{1e-9*stop_time}')

def monitor(buffer: SharedRingBuffer):
    while True:
        print(buffer.size(), flush = True)
        if buffer.overflow.is_set():
            print('OVERFLOW', flush=True)
        time.sleep(0.01)

def producer(buffer: SharedRingBuffer, nloop: int, rate: float):
    for i in range(nloop):
        _ , buf = buffer.get_write_buffer()
        buf[:] = BIG_ARRAY.reshape((BIG_ARRAY.nbytes,))
        buffer.write_done()
        time.sleep(rate)

if __name__ == '__main__':
    mp.set_start_method('spawn')

    # shared ring buffer 
    buffer = SharedRingBuffer(
        num_element=10, 
        element_size=BIG_ARRAY.nbytes,
        packer=None,
        unpacker=None
    )

    mon = Process(target=monitor, args=(buffer, ))
    cons = Process(target=consumer, args=(buffer, NLOOP))
    prod = Process(target=producer, args=(buffer, NLOOP, 0.01))
    cons.start()
    mon.start()
    prod.start()
    prod.join()
    cons.join()
    mon.terminate()
  