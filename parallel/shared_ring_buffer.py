from multiprocessing import Array, Value, Event 
from typing import List
import time
from itertools import cycle

class SharedRingBuffer:

    def __init__(
            self,
            num_element: int,
            element_byte_size: int
        ):

        self.element_byte_size = element_byte_size
        self.num_element = num_element
        self.total_size = element_byte_size * num_element

        self.read_cursor = Value('i',0)
        self.write_cursor = Value('i',0)
        self.data_available = Event()
        self.data = Array('B', self.total_size)

    def get_read_buffer(self):
        '''return memoryview to the current read location'''
        buffer = memoryview(self.data.get_obj()).cast('B')
        empty = self.empty()
        slice = buffer[self.read_cursor.value:self.read_cursor.value+self.element_byte_size]
        return (empty, slice)

    def get_write_buffer(self):
        '''return memoryview to the current write location'''
        buffer = memoryview(self.data.get_obj()).cast('B')
        full = self.full()
        slice = buffer[self.write_cursor.value:self.write_cursor.value+self.element_byte_size]
        return (full, slice)
    
    def read_done(self):
        '''current position has been read'''
        self.read_cursor.value = (self.read_cursor.value  +  self.element_byte_size) % self.total_size
        if self.empty():
            self.data_available.clear()

    def write_done(self):
        '''current position has been written'''
        self.write_cursor.value = (self.write_cursor.value  +  self.element_byte_size) % self.total_size
        self.data_available.set()

    def full(self):
        ''' check if buffer is full '''
        return self.write_cursor.value == ((self.read_cursor.value - self.element_byte_size) % self.total_size)

    def empty(self):
        ''' check if buffer is empty '''
        return self.write_cursor.value == self.read_cursor.value

    def size(self):
        ''' Return number of items currently stored in the buffer '''
        num_bytes = (self.write_cursor.value - self.read_cursor.value) % self.total_size
        numel = num_bytes/self.element_byte_size
        return numel
    

# maybe that can be separated in input and output buffers ?
class BufferCollection:
    def __init__(
            self,
            buffer_collection: List[SharedRingBuffer],
            dispatch = True,
            timeout = 1,
            dt = 0.1
        ) -> None:

        self.buffer_collection = buffer_collection
        self.dispatch = dispatch
        self.timeout = timeout
        self.dt = dt

        self.data_available = [(idx, buffer.data_available) for (idx, buffer) in enumerate(buffer_collection)]
        self.event_iterator = cycle(self.data_available)

        self.buffer_iterator = cycle(self.buffer_collection)

    def select(self):
        start_time = time.time()
        while True:
            counter = 0
            for idx, event in self.event_iterator:
                if event.is_set():
                    return self.buffer_collection[idx]
                counter += 1
                # if we tried all of them unsuccessfully, sleep a bit
                if counter == len(self.buffer_collection):
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
        return self.buffer_collection

    def write_dispatch(self) -> List[SharedRingBuffer]:
        return [next(self.buffer_iterator)]

        
