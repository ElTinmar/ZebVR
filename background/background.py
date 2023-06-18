from scipy import stats
from numpy.typing import NDArray
import cv2
from core.abstractclasses import Background
from multiprocessing import Process, Event
from multiprocessing.sharedctypes import Array, Value
import numpy as np
import ctypes

class BoundedQueue:
    def __init__(self, size, maxlen):
        self.size = size
        self.maxlen = maxlen
        self.itemsize = np.prod(size)

        self.numel = Value('i',0)
        self.insert_ind = Value('i',0)
        self.data = Array(ctypes.c_float, int(self.itemsize*maxlen))
    
    def append(self, item) -> None:
        data_np = np.frombuffer(self.data.get_obj(), dtype=np.float32).reshape((self.maxlen, *self.size))
        np.copyto(data_np[self.insert_ind.value,:,:],item)
        self.numel.value = min(self.numel.value+1, self.maxlen) 
        self.insert_ind.value = (self.insert_ind.value + 1) % self.maxlen

    def get_data(self):
        if self.numel.value == 0:
            return None
        else:
            data_np = np.frombuffer(self.data.get_obj(), dtype=np.float32).reshape((self.maxlen, *self.size))
            return data_np[0:self.numel.value,:,:]

class DynamicBackground(Background):
    def __init__(
        self, 
        width,
        height,
        num_images = 500, 
        every_n_image = 100,
        polarity: int = 1,
        rescale = None
    ) -> None:

        self.width = width
        self.height = height
        self.num_images = num_images
        self.every_n_image = every_n_image
        self.counter = 0
        self.polarity = polarity
        self.rescale = rescale
        
        self.stop_flag = Event()
        self.background = Array(ctypes.c_float, width*height)
        self.image_store = BoundedQueue((width,height),maxlen=num_images)

    def start(self):
        self.proc_display = Process(
            target=self.show_background,
            args=(self.width, self.height, self.rescale, self.stop_flag, self.background)
        )
        self.proc_display.start()

        self.proc_compute = Process(
            target=self.compute_background, 
            args=(self.stop_flag, self.image_store, self.background)
        )
        self.proc_compute.start()
        
    def stop(self):
        self.stop_flag.set()
        self.proc_compute.join()
        self.proc_display.join()

    @staticmethod
    def show_background(
        width: int, 
        height: int,
        rescale: float, 
        stop_flag: Event, 
        background: Array
    ):

        cv2.namedWindow('background')
        while not stop_flag.is_set():
            bckg = np.frombuffer(background.get_obj(), dtype=np.float32).reshape(width,height)
            if rescale is not None:
                smallimg = cv2.resize(
                    bckg, 
                    None, 
                    fx = rescale, 
                    fy = rescale,
                    interpolation=cv2.INTER_NEAREST
                )
                cv2.imshow('background',smallimg)
            else:
                cv2.imshow('background',bckg)

            cv2.waitKey(16)
        cv2.destroyWindow('background')

    @staticmethod
    def compute_background(
        stop_flag: Event, 
        image_store: BoundedQueue, 
        background: Array
    ):

        while not stop_flag.is_set():
            data = image_store.get_data()
            if data is not None:
                bckg_img = stats.mode(data, axis=0, keepdims=False).mode
                background[:] = bckg_img.flatten()

    def get_background(self) -> NDArray:
        return np.frombuffer(self.background.get_obj(), dtype=np.float32).reshape((self.width,self.height))
    
    def add_image(self, image : NDArray) -> None:
        """
        Input an image and update the background model
        """
        if self.counter % self.every_n_image == 0:
            self.image_store.append(image)
            if self.counter == 0:
                self.background[:] = image.flatten()
        self.counter += 1

    def get_polarity(self) -> int:
        return self.polarity