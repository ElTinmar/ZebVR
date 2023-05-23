from writers.writer import Writer
import cv2

class PNG_writer(Writer):
    def __init__(self, compression = 1):
        if not 0 <= compression <= 9:
            ValueError('compression should be between 0 and 9')
        self._compression = compression
    
    def write(self, filename, img):
        cv2.imwrite(
            filename + '.png',  
            img, 
            [cv2.IMWRITE_PNG_COMPRESSION, self._compression]
        )