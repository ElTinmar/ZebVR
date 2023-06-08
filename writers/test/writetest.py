from writers.jpg import JPG_writer
from writers.png import PNG_writer
from writers.tiff import TIFF_writer
from writers.raw_array import RawArray_writer
from writers.video import CVWriter
import numpy as np

# image writers
prefix = '/home/martin/Documents/test'
writer_list = [JPG_writer,PNG_writer,RawArray_writer,TIFF_writer]

for W in writer_list:
    writer = W(prefix=prefix)
    for i in range(100):
        X = np.random.rand(1024,1024)
        writer.write(X)

# video writer
writer = CVWriter(
    height = 1024,
    width = 1024,
    fps = 100,
    filename = prefix + '/video.avi'
)

writer.start()
for i in range(1000):
    X = np.random.rand(1024,1024)
    writer.write(X)
writer.stop()
