from multiprocessing import Array, Value, Event 
from typing import List, Callable, Optional, Any
import time
from itertools import cycle
import numpy as np

class SharedRingBuffer:

    def __init__(
            self,
            num_element: int,
            element_size: int,
            packer: Callable,
            unpacker: Callable,
            data_type = 'B'
        ):

        self.num_element = num_element
        self.element_size = element_size
        self.packer = packer
        self.unpacker = unpacker
        self.total_size = element_size * num_element
        self.data_type = data_type
        
        # NOTE: unsigned long int can overflow, 
        # which can cause problems if the buffer
        # is too big. I should run out of memory
        # before this becomes a problem though
        self.read_cursor = Value('I',0)
        self.write_cursor = Value('I',0)
        self.data_available = Event()
        self.overflow = Event()
        self.data = Array(data_type, self.total_size)

    def get_read_buffer(self):
        '''return buffer to the current read location'''
        buffer = np.frombuffer(
            self.data.get_obj(), 
            dtype = self.data_type, 
            count = self.element_size,
            offset = self.read_cursor.value * self.element_size 
        )
        empty = self.empty()
        return (empty, buffer)

    def get_write_buffer(self):
        '''return buffer to the current write location'''
        buffer = np.frombuffer(
            self.data.get_obj(), 
            dtype = self.data_type, 
            count = self.element_size,
            offset = self.write_cursor.value * self.element_size
        )
        full = self.full()
        return (full, buffer)
    
    def read_done(self):
        '''current position has been read'''
        self.read_cursor.value = (self.read_cursor.value  +  1) % self.num_element
        if self.empty():
            self.data_available.clear()

    def write_done(self):
        '''current position has been written'''
        if self.full():
            self.overflow.set()
        self.write_cursor.value = (self.write_cursor.value  +  1) % self.num_element
        self.data_available.set()

    def full(self):
        ''' check if buffer is full '''
        return self.write_cursor.value == ((self.read_cursor.value - 1) % self.num_element)

    def empty(self):
        ''' check if buffer is empty '''
        return self.write_cursor.value == self.read_cursor.value

    def size(self):
        ''' Return number of items currently stored in the buffer '''
        return (self.write_cursor.value - self.read_cursor.value) % self.num_element
    
    def pack(self, *args, **kwargs) -> Any:
        full, data = self.get_write_buffer()
        return self.packer(data, *args, **kwargs)
    
    def unpack(self) -> Any:
        empty, data = self.get_read_buffer()
        return self.unpacker(data)

class DataDispatcher:
    '''
    contains collections of buffers and their respective packing and unpacking functions
    handles buffer dispatching/copy and load balancing 
    '''
    def __init__(
            self,
            buffers: List[SharedRingBuffer],
            dispatch = True,
            timeout = 1,
            dt = 0.1
        ) -> None:

        self.buffers = buffers
        self.dispatch = dispatch
        self.timeout = timeout
        self.dt = dt

        self.data_available = [(idx, buffer.data_available) for (idx, buffer) in enumerate(buffers)]
        self.event_iterator = cycle(self.data_available)
        self.buffer_iterator = cycle(self.buffers)

    def select(self) -> Optional[SharedRingBuffer]:
        start_time = time.time()
        while True:
            counter = 0
            for idx, event in self.event_iterator:
                if event.is_set():
                    return self.buffers[idx]
                counter += 1
                # if we tried all of them unsuccessfully, sleep a bit
                if counter == len(self.buffers):
                    break

            elapsed_time = time.time() - start_time
            if elapsed_time >= self.timeout:
                return None
            
            time.sleep(self.dt)
        
    def read(self) -> SharedRingBuffer:
        return self.select()
    
    def write(self) -> List[SharedRingBuffer]:
        if self.dispatch:
            return self.write_dispatch()
        else:
            return self.write_copy()

    def write_copy(self) -> List[SharedRingBuffer]:
        return self.buffers

    def write_dispatch(self) -> List[SharedRingBuffer]:
        return [next(self.buffer_iterator)]

        
