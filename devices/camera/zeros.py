from devices.camera.camera import Camera, BufferAdapter
import time
import numpy as np

class Buffer(BufferAdapter):
    def __init__(self, image, timestamp):
        self._image = image
        self._timestamp = timestamp

    def get_img(self):
        return self._image
    
    def get_timestamp(self):
        return self._timestamp

    def queue(self):
        pass

class Zeros(Camera):
    """
    Provides an empty image. This is just for testing
    """

    def __init__(self, ini_file):
        super().__init__(ini_file)

    def start_acquisition(self):
        pass

    def stop_acquisition(self):
        pass

    def fetch(self):
        ts = int(time.time())
        img = np.zeros((self._width, self._height), dtype=np.uint8)
        buf = Buffer(img,ts)

        # do a fake exposure
        time.sleep(self._exposure_time * 1e-6)
        return buf
