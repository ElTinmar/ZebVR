import cv2
import numpy as np

duration_sec = 5
fps = 120
sz = (1140, 912)
color = True
num_frames = duration_sec * fps

writer = cv2.VideoWriter(f'clock_{fps}Hz.avi', cv2.VideoWriter_fourcc(*'MJPG'), fps, sz, color)

org = (sz[0]//3, sz[1]//2)
font = cv2.FONT_HERSHEY_SIMPLEX
fontScale = 5
mod = fps//15
colors = np.vstack((
    np.linspace(0,255,mod, dtype=np.uint8), 
    np.zeros((8,), dtype=np.uint8), 
    np.linspace(255,0,mod, dtype=np.uint8)
))
thickness = 15
anti_aliasing = cv2.LINE_AA

for i in range(num_frames):
    col = (int(colors[0,i%mod]), int(colors[1,i%mod]), int(colors[2,i%mod]))
    frame = np.zeros((sz[1],sz[0],3), dtype=np.uint8)
    frame = cv2.putText(frame, str(i), org, font, fontScale, col, thickness, anti_aliasing) 
    writer.write(frame)

writer.release()