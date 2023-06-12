from devices.projector.opencv_projector import CVProjector
import numpy as np
import cv2
import time

N = 100
color = True

# create movie
if color:
    X  = np.random.rand(1024,1024,3,N)
else:
    X  = np.random.rand(1024,1024,N)

# projector
projector = CVProjector(monitor_id = 1)
projector.init_window()
start_time_ns = time.process_time_ns()
for i in range(N):
    projector.project(X[:,:,:,i])
duration =1e-9*(time.process_time_ns() - start_time_ns)/N
print(f'projector {duration}')
projector.close_window()

# bare opencv
cv2.namedWindow('direct')
start_time_ns = time.process_time_ns()
for i in range(N):
    cv2.imshow('direct',X[:,:,:,i])
    cv2.waitKey(1)
duration = 1e-9*(time.process_time_ns() - start_time_ns)/N
print(f'direct {duration}')
cv2.destroyWindow('direct')

