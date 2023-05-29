from collections import deque
from scipy import stats
from numpy.typing import NDArray
import cv2

class StaticBackground:
    """
    take images at the beginning of the recording to
    create a backgroud image
    """
    def __init__(self, num_images = 500, every_n_image = 100) -> None:
        self.num_images = num_images
        self.every_n_image = every_n_image
        self.image_store = deque(maxlen=num_images)
        self.background = None
        self.complete = False
        self.counter = 0

        cv2.namedWindow('background')
        
    def add_image(self, image : NDArray) -> None:
        """
        Input an image and update the background model
        """
        if self.complete:
            pass
        else:
            if self.counter % self.every_n_image == 0:
                if len(self.image_store) < self.num_images:
                    self.image_store.append(image)
                    self.counter += 1
                    if len(self.image_store) == 1:
                        self.background = image

                if len(self.image_store) == self.num_images:
                    self.background = stats.mode(self.image_store, axis=0, keepdims=False).mode
                    self.complete = True

    def get_background(self) -> NDArray:
        """
        Outputs a background image
        """

        cv2.imshow('background',self.background)
        cv2.waitKey(1)

        return self.background
class DynamicBackground:
    """
    take images at regular intervals during the recording and
    update the backgroud image
    """
    def __init__(self, num_images = 500, every_n_image = 100) -> None:
        self.num_images = num_images
        self.every_n_image = every_n_image
        self.image_store = deque(maxlen=num_images)
        self.counter = 0
        self.background = None

        cv2.namedWindow('background')
        
    def add_image(self, image : NDArray) -> None:
        """
        Input an image and update the background model
        """
        if self.counter % self.every_n_image == 0:
            self.image_store.append(image)
            if len(self.image_store) == 1:
                self.background = self.image_store[0]
            else:
                self.background = stats.mode(self.image_store, axis=0, keepdims=False).mode
        self.counter += 1

    def get_background(self) -> NDArray:
        """
        Outputs a background image
        """

        cv2.imshow('background',self.background)
        cv2.waitKey(1)

        return self.background