import numpy as np
from video_tools import OpenCV_VideoWriter
import glob

writer = OpenCV_VideoWriter(            
    height=512, 
    width=512, 
    fps=60, 
    filename = 'output.avi'
)

files = sorted(glob.glob('recording_0/*.npz'))
for f in files:
    data = np.load(f)
    img = data['image']
    writer.write_frame(img)
writer.close()