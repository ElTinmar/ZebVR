import cv2
import numpy as np

duration_sec = 5
fps = 120
sz = (1140, 912)
color = True
num_frames = duration_sec * fps

writer = cv2.VideoWriter(f'clock_{fps}Hz_gray.avi', cv2.VideoWriter_fourcc(*'MJPG'), fps, sz, color)

org = (sz[0]//3, sz[1]//2)
font = cv2.FONT_HERSHEY_SIMPLEX
fontScale = 5
thickness = 15
anti_aliasing = cv2.LINE_AA

for i in range(num_frames):
    frame = np.zeros((sz[1],sz[0],3), dtype=np.uint8)
    frame = cv2.putText(frame, str(i), org, font, fontScale, (255,255,255), thickness, anti_aliasing) 
    writer.write(frame)

writer.release()