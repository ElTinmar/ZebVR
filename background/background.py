from collections import deque
from scipy import stats
from numpy.typing import NDArray

class Background:
    def __init__(self, num_images = 500, every_n_image = 100) -> None:
        self.num_images = num_images
        self.every_n_image = every_n_image
        self.image_store = deque(maxlen=num_images)
        self.counter = 0
        
    def add_image(self, image : NDArray) -> None:
        """
        Input an image to update the background model
        """
        self.counter += 1
        if self.counter % self.every_n_image == 0:
            self.image_store.append(image)

    def get_background(self) -> NDArray:
        """
        Outputs a background image
        """
        if len(self.image_store) == 1:
            res = self.image_store[0]
        else:
            res = stats.mode(self.image_store, axis=0, keepdims=False).mode
        return res