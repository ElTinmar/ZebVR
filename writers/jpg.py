from writers.writer import Writer
import cv2

class JPG_writer(Writer):
    def __init__(self, quality = 95):
        self._quality = quality
    
    def write(self, filename, img):
        cv2.imwrite(
            filename + '.jpg',  
            img, 
            [cv2.IMWRITE_JPEG_QUALITY, self._quality]
        )