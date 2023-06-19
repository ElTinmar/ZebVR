from devices.projector.opencv_projector import CVProjector
import numpy as np
import cv2
import time

N = 100
color = True

# create movie
if color:
    X  = np.random.rand(1440,2560,3,N)
else:
    X  = np.random.rand(1440,2560,N)

# projector opencv 
projector = CVProjector(monitor_id = 1)
projector.init_window()
start_time_ns = time.time_ns()
for i in range(N):
    if color:
        projector.project(X[:,:,:,i])
    else:
        projector.project(X[:,:,i])
duration =1e-9*(time.time_ns() - start_time_ns)/N
print(f'projector {duration}')
projector.close_window()

# bare opencv
cv2.namedWindow('direct')
start_time_ns = time.time_ns()
for i in range(N):
    if color:
        cv2.imshow('direct',X[:,:,:,i])
    else:
        cv2.imshow('direct',X[:,:,i])
    cv2.waitKey(1)
duration = 1e-9*(time.time_ns() - start_time_ns)/N
print(f'direct {duration}')
cv2.destroyWindow('direct')

# projector psychopy
from devices.projector.psychopy_projector import PsychoPyProjector
projector = PsychoPyProjector(monitor_id = 0)
projector.init_window()
start_time_ns = time.time_ns()
for i in range(N):
    if color:
        projector.project(X[:,:,:,i])
    else:
        projector.project(X[:,:,i])
duration =1e-9*(time.time_ns() - start_time_ns)/N
print(f'projector {duration}')
projector.close_window()

"""
The conclusion is that I shouldn't create an image and 
then display it, but use OpenGL capabilities either 
directly by writing shaders, or through python 
libraries (pyglet,psychopy,...) 
"""