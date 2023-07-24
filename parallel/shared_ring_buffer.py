from multiprocessing import Array, Value, Event 

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
        return (self.write_cursor.value - self.read_cursor.value) % self.total_size