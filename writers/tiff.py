from writers.writer import Writer
import cv2
from enum import Enum

class TiffCompression(Enum):
    COMPRESSION_NONE = 1
    COMPRESSION_LZW = 5
    COMPRESSION_ADOBE_DEFLATE = 8
    COMPRESSION_DEFLATE = 32946
    COMPRESSION_JP2000 = 34712

class TIFF_writer(Writer):
    def __init__(self, compression_type = TiffCompression.COMPRESSION_LZW):
        if compression_type not in TiffCompression:
            ValueError('Use TiffCompression enum')
        self.compression_type = compression_type
    
    def write(self, filename, img):
        # TODO check that filename extension is '.tiff'
        cv2.imwrite(
            filename + '.tiff',  
            img, 
            [cv2.IMWRITE_TIFF_COMPRESSION, self.compression_type]
        )