import cv2
import numpy as np
from numpy.typing import NDArray
from scipy import stats
from typing import Protocol, Tuple
from utils.im2gray import im2gray
from utils.im2float import im2single

class VideoReader(Protocol):
    def next_frame(self) -> Tuple[bool,NDArray]:
        """return the next frame in the movie, 
        and a boolean if the operation succeeded"""

    def get_number_of_frame(self) -> int:
        """return number of frames in the movie"""

    def seek_to(self, index) -> None:
        """go to a specific frame retrieveable with a call to next_frame"""

    def get_width(self) -> int:
        """return width"""
    
    def get_height(self) -> int:
        """return height"""

    def get_num_channels(self) -> int:
        """return number of channels"""

    def get_type(self) -> np.dtype:
        """return data type"""

def sample_frames_evenly(video_reader: VideoReader, k=500):
    height = video_reader.get_height()
    width = video_reader.get_width()
    numframes = video_reader.get_number_of_frame()
    sample_indices = np.linspace(0, numframes-1, k, dtype = np.int64)
    sample_frames = np.empty((height, width, k), dtype=np.float32)
    for i,index in enumerate(sample_indices):
        video_reader.seek_to(index)
        rval, frame = video_reader.next_frame()
        sample_frames[:,:,i] = im2single(im2gray(frame))
    return sample_frames

def background_model_mode(sample_frames):
    """
    Take sample images from the video and return the mode for each pixel
    Input:
        sample_frames: m x n x k numpy.float32 array where k is the number of 
        frames
    Output:
        background: m x n numpy.float32 array
    """
    return stats.mode(sample_frames,axis=2,keepdims=False).mode