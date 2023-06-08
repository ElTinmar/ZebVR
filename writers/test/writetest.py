from writers.jpg import JPG_writer
from writers.png import PNG_writer
from writers.tiff import TIFF_writer
from writers.raw_array import RawArray_writer
import numpy as np

prefix = '/home/martin/Documents/test'
writer_list = [JPG_writer,PNG_writer,RawArray_writer,TIFF_writer]

for W in writer_list:
    writer = W(prefix=prefix)
    for i in range(100):
        X = np.random.rand(1024,1024)
        writer.write(X)
