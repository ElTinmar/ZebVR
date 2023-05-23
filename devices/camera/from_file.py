from devices.camera.camera import Camera, BufferAdapter
import time
import cv2
import logging
import numpy as np

class BufferFromImg(BufferAdapter):
    def __init__(self, image, timestamp):
        self._image = image
        self._timestamp = timestamp

    def get_img(self):
        return self._image
    
    def get_timestamp(self):
        return self._timestamp

    def queue(self):
        """This is important to allow the camera to reuse the buffer"""
        pass

class FromFile(Camera):
    def __init__(self, ini_file, video_file):
        super().__init__(ini_file)
        self._video_file = video_file
        self._cap = cv2.VideoCapture(video_file)
        self._img_count = np.uint64(0)

    def start_acquisition(self):
        pass

    def stop_acquisition(self):
        pass

    def fetch(self):
        self._img_count += np.uint64(1)
        self._logger.log(logging.DEBUG, f'FromFile, {time.time_ns()}, {self._img_count}, 0')
        ret, img = self._cap.read()
        img_gray = img[:,:,0]
        buf = BufferFromImg(img_gray, self._img_count)  
        self._logger.log(logging.DEBUG, f'FromFile, {time.time_ns()}, {self._img_count}, 1')

        # do a fake exposure
        #time.sleep(1/self._fps)
        return buf

    def __del__(self):
        self._cap.release()