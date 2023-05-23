from writers.writer import Writer
import cv2
from multiprocessing import Process, Value, shared_memory

class Video_writer(Writer):
    def __init__(self, num_buffers, height, width, fps, videoname):

        # create a shared memory buffer to queue frames for video
        # compression
        self._videoWriter_buffers = shared_memory.SharedMemory(
            name='videoWriter_buffers', 
            create=True, 
            size=num_buffers*height*width
        )
        self._size = Value('i', 0)
        self._fps = fps
        fourcc = cv2.VideoWriter_fourcc(*'H264')
        self._cap = cv2.VideoWriter(videoname,fourcc,fps,(width,height))

    def start(self):
        while True:
            if self._size > 0:
                pass

    def write(self, filename, img):
        if self._size == num_buffers-1:
            # the buffer is full, wait 

        else:    
            self._videoWriter_buffers[]
