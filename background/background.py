from collections import deque
from scipy import stats
from numpy.typing import NDArray
import cv2
from core.abstractclasses import Background
from multiprocessing import Process, Event
from multiprocessing.sharedctypes import Array
import numpy as np

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
        self.image_store = deque(maxlen=num_images) # TODO need to share that as well
        self.counter = 0

        self.background = Array('d',(width,height))
        self.image_store = Array('d',(num_images,width,height))
        self.stop_flag = Event()
        self.proc = Process(target=self.compute_background)
        self.proc.start()

    def compute_background(self):
        while not self.stop_flag.is_set():
            if len(self.image_store)>0:
                self.background = stats.mode(self.image_store, axis=0, keepdims=False).mode

    def get_background(self) -> NDArray:
        return np.asarray(self.background)
    
    def add_image(self, image : NDArray) -> None:
        """
        Input an image and update the background model
        """

        if self.counter % self.every_n_image == 0:
            self.image_store.append(image)
            if len(self.image_store) == 1:
                self.background = self.image_store[0]
        self.counter += 1

    def __del__(self):
        self.stop_flag.set()
        self.proc.join()
    