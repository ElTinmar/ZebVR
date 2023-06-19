import cv2
import numpy as np
import time

X = np.random.rand(1200,1900)
cv2.namedWindow('test')

def test_fps(fps = 60):
    counter = 0
    while counter < 100:
        start_time_ns = time.time_ns()
        cv2.imshow('test', X)
        cv2.waitKey(1)
        counter += 1
        if 1e-9*(time.time_ns()-start_time_ns) > 1/fps:
            print('too slow')
        else:
            while 1e-9*(time.time_ns()-start_time_ns) < 1/fps:
                pass

%timeit test_fps(20)