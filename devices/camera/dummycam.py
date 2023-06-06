from core.abstractclasses import CameraData, Camera
import cv2
import time
import numpy as np
import logging
import time

class Data(CameraData):
    def __init__(self, image, index, timestamp):
        # transform image to single precision
        ui_info = np.iinfo(image.dtype)
        self.image = image.astype(np.float32) / ui_info.max
        self.timestamp = timestamp
        self.index = index

    def get_img(self):
        return self.image
    
    def get_index(self):
        return self.index 
    
    def get_timestamp(self):
        return self.timestamp

    def reallocate(self):
        pass

class FromFile(Camera):
    def __init__(self, video_file, **kwargs):
        super().__init__(**kwargs)
        self.video_file = video_file
        self.cap = cv2.VideoCapture(video_file)
        self.img_count = 0

    def start_acquisition(self):
        pass

    def stop_acquisition(self):
        pass

    def fetch(self):
        start_time_ns = time.process_time_ns()
        self.img_count += 1
        self.logger.log(logging.DEBUG, f'FromFile, {time.time_ns()}, {self.img_count}, 0')
        ret, img = self.cap.read()
        if ret:
            img_gray = img[:,:,0]
            buf = Data(
                image = img_gray, 
                index = self.img_count, 
                timestamp = self.img_count/self.parameters.fps
            )  
            self.logger.log(logging.DEBUG, f'FromFile, {time.time_ns()}, {self.img_count}, 1')

            while time.process_time_ns() - start_time_ns < 1e9/self.parameters.fps:
                pass

            return (buf, ret)
        else:
            return (None, ret)

    def __del__(self):
        self.cap.release()

class ZeroCam(Camera):
    """
    Provides an empty image. This is just for testing
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.img_count = 0

    def start_acquisition(self):
        pass

    def stop_acquisition(self):
        pass

    def fetch(self):
        self.img_count += 1
        img = np.zeros((self.parameters.ROI_width, self.parameters.ROI_height), dtype=np.uint8)
        buf = Data(img, self.img_count)
        return (buf, True)
    
class RandomCam(Camera):
    """
    Provides an empty image. This is just for testing
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.img_count = 0

    def start_acquisition(self):
        pass

    def stop_acquisition(self):
        pass

    def fetch(self):
        self.img_count += 1
        img = np.random.randint(0, 255, (self.parameters.ROI_width, self.parameters.ROI_height), dtype=np.uint8)
        buf = Data(img, self.img_count)
        return (buf, True)
