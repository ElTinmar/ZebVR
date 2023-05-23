from writers.writer import Writer
import numpy as np

class RawArray_writer(Writer):
    """
    Definitely faster than using cv2.imwrite with JPG2000 compression
    but generates large annoying files.
    For 1024x1024 @ 200Hz it's around 1TB per hour  
    """
    def write(self, filename, img):
        img.tofile(filename + '.nparray')