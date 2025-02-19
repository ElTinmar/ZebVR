import numpy as np
from video_tools import OpenCV_VideoWriter
import glob
from tqdm import tqdm

if __name__ == '__main__':

    from ..config import (
        CAM_HEIGHT,
        CAM_WIDTH,
        VIDEO_RECORDING_FPS,
        VIDEO_RECORDING_RESIZE
    )

    writer = OpenCV_VideoWriter(            
        height=int(CAM_HEIGHT*VIDEO_RECORDING_RESIZE), 
        width=int(CAM_WIDTH*VIDEO_RECORDING_RESIZE), 
        fps=VIDEO_RECORDING_FPS, 
        filename = 'output.avi'
    )

    files = sorted(glob.glob('recording_0/*.npz'))
    for f in tqdm(files):
        data = np.load(f)
        # metadata = data['metadata']
        img = data['image']
        writer.write_frame(img)
    writer.close()