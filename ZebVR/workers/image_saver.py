from dagline import WorkerNode
import numpy as np
from numpy.typing import NDArray
from typing import Any
import cv2
import os
import time
from video_tools import FFMPEG_VideoWriter_CPU, FFMPEG_VideoWriter_GPU 

#TODO: check zarr, maybe try cv2.imwrite

class ImageSaverWorker(WorkerNode):

    def __init__(
            self, 
            folder: str, 
            fps: int = 10,
            zero_padding: int = 8, 
            resize: float = 0.25,
            compress: bool = False, 
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        
        self.folder = folder
        self.fps = fps
        self.resize = resize
        self.zero_padding = zero_padding
        self.compress = compress
        self.prev_time = 0

    def initialize(self) -> None:
        super().initialize()
        if not os.path.exists(self.folder):
            os.mkdir(self.folder)

    def process_data(self, data: NDArray) -> None:

        if data is not None:

            if time.monotonic() - self.prev_time > 1/self.fps:
                
                image_resized = cv2.resize(data['image'],None,None,self.resize,self.resize,cv2.INTER_NEAREST)
                metadata = data[['index','timestamp']]
                filename = os.path.join(self.folder, f"{data['index']:0{self.zero_padding}}")
                
                if self.compress:
                    np.savez_compressed(filename, image=image_resized, metadata=metadata)
                else:
                    np.savez(filename, image=image_resized, metadata=metadata)

                self.prev_time = time.monotonic()

    def process_metadata(self, metadata) -> Any:
        pass

class VideoSaverWorker(WorkerNode):
    
    SUPPORTED_CODECS_CPU = ['libx264', 'hevc']
    SUPPORTED_CODECS_GPU = ['h264_nvenc', 'hevc_nvenc']

    def __init__(
            self, 
            height: int, # final height of the recorded video: images will be rescaled to that size
            width: int, # final width of the recorded video: images will be rescaled to that size
            filename: str, 
            fps: int = 30,
            codec: str = 'libx264', 
            gpu: bool = False,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        
        self.filename = filename
        self.fps = fps
        self.height = 2*(height//2) # some codecs require images with even size
        self.width = 2*(width//2)
        
        if gpu and (not codec in self.SUPPORTED_CODECS_GPU):
            raise ValueError(f'wrong codec type for GPU encoding, supported codecs are: {self.SUPPORTED_CODECS_GPU}') 

        if (not gpu) and (not codec in self.SUPPORTED_CODECS_CPU):
            raise ValueError(f'wrong codec type for CPU encoding, supported codecs are: {self.SUPPORTED_CODECS_CPU}')
    
        self.codec = codec
        self.gpu = gpu
        self.writer = None

    def initialize(self) -> None:

        super().initialize()
        
        if self.gpu:
            self.writer = FFMPEG_VideoWriter_GPU(
                height = self.height, 
                width = self.width, 
                fps = self.fps, 
                q = 23,
                filename = self.filename,
                codec = self.codec,
                profile = 'baseline',
                preset = 'p2'
            )

        else:
            self.writer = FFMPEG_VideoWriter_CPU(
                height = self.height, 
                width = self.width, 
                fps = self.fps, 
                q = 23,
                filename = self.filename,
                codec = self.codec,
                profile = 'baseline',
                preset = 'veryfast'
            )

    def cleanup(self) -> None:

        super().cleanup()
        self.writer.close()

    def process_data(self, data: NDArray) -> None:

        if data is not None:
            image_resized = cv2.resize(data['image'], (self.width, self.height), interpolation = cv2.INTER_NEAREST)
            self.writer.write_frame(image_resized)

    def process_metadata(self, metadata) -> Any:
        pass