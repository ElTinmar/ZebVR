from collections import deque
from scipy import stats
from numpy.typing import NDArray
import cv2
from core.abstractclasses import Background
from multiprocessing import Process, Event
from multiprocessing.sharedctypes import Array, Value
import numpy as np

class BoundedQueue:
    def __init__(self, size, maxlen):
        self.size = size
        self.maxlen = maxlen
        self.itemsize = np.prod(size)
        self.numel = Value('i',0)
        self.insert_ind = Value('i',0)
        self.data = Array('d', int(self.itemsize*maxlen))
    
    def append(self, item) -> None:
        self.data[self.insert_ind.value*self.itemsize:(self.insert_ind.value+1)*self.itemsize] = item.flatten()
        self.numel.value += 1 
        self.insert_ind.value = (self.insert_ind.value + 1) % self.maxlen

    def get_data(self):
        if self.numel.value == 0:
            return []
        else:
            images = np.asarray(self.data[0:self.numel.value*self.itemsize])
            return images.reshape((*self.size,self.numel.value))

class DynamicBackground(Background):
    def __init__(
        self, 
        width,
        height,
        num_images = 500, 
        every_n_image = 100
    ) -> None:

        self.num_images = num_images
        self.every_n_image = every_n_image
        self.counter = 0

        self.background = Array('d',(width,height))
        self.stop_flag = Event()
        self.image_store = BoundedQueue((width,height),maxlen=num_images)
        self.proc = Process(target=self.compute_background)
        self.proc.start()
        
    def compute_background(self):

        cv2.namedWindow('background')

        while not self.stop_flag.is_set():
            data = self.image_store.get_data()
            if len(data)>0:
                self.background = stats.mode(data, axis=2, keepdims=False).mode
                cv2.imshow('background',self.background)
                cv2.waitKey(1)

        cv2.destroyWindow('background')

    def get_background(self) -> NDArray:
        return np.asarray(self.background)
    
    def add_image(self, image : NDArray) -> None:
        """
        Input an image and update the background model
        """

        if self.counter % self.every_n_image == 0:
            self.image_store.append(image)
            if self.counter == 0:
                self.background = image
        self.counter += 1

    def __del__(self):
        self.stop_flag.set()
        self.proc.join()
    