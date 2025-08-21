from dagline import WorkerNode
import numpy as np
from numpy.typing import NDArray
from typing import Any, Union
import cv2
import os
from pathlib import Path
from video_tools import (
    FFMPEG_VideoWriter_CPU_YUV420P, 
    FFMPEG_VideoWriter_GPU_YUV420P,
    FFMPEG_VideoWriter_CPU_Grayscale
)
import time
from ZebVR.utils import append_timestamp_to_filename

# TODO: check zarr, maybe try cv2.imwrite

class ImageSaverWorker(WorkerNode):

    def __init__(
            self, 
            folder: Union[str, Path], 
            decimation: int = 1,
            zero_padding: int = 8, 
            resize: float = 0.25,
            compress: bool = False, 
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        
        self.folder = Path(folder)
        self.decimation = decimation
        self.resize = resize
        self.zero_padding = zero_padding
        self.compress = compress

    def initialize(self) -> None:
        super().initialize()
        if not self.folder.exists():
            os.mkdir(self.folder)

    def process_data(self, data: NDArray) -> None:

        if data is None:
            return

        if data['index'] % self.decimation == 0:
            
            image_resized = cv2.resize(data['image'],None,None,self.resize,self.resize,cv2.INTER_NEAREST)
            metadata = data[['index','timestamp']]
            filename = self.folder / f"{data['index']:0{self.zero_padding}}"
            
            if self.compress:
                np.savez_compressed(filename, image=image_resized, metadata=metadata)
            else:
                np.savez(filename, image=image_resized, metadata=metadata)
            
            return data

    def process_metadata(self, metadata) -> Any:
        pass

class VideoSaverWorker(WorkerNode):
    
    SUPPORTED_VIDEO_CODECS_GRAYSCALE = ['h264']
    SUPPORTED_VIDEO_CODECS_CPU = ['h264', 'hevc', 'mjpeg']
    SUPPORTED_VIDEO_CODECS_GPU = ['h264_nvenc', 'hevc_nvenc']

    def __init__(
            self, 
            height: int, # final height of the recorded video: images will be rescaled to that size
            width: int, # final width of the recorded video: images will be rescaled to that size
            filename: Union[str, Path], 
            decimation: int = 1,
            fps: int = 30,
            video_quality: int = 23,
            video_codec: str = 'h264', 
            video_profile: str = 'main',
            video_preset: str = 'p2',
            gpu: bool = False,
            grayscale: bool = False,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        
        video_filename = append_timestamp_to_filename(filename)
        self.video_filename = video_filename
        self.timings_filename = video_filename.stem + '.csv' # TODO: this is not saved in the right location
        self.fps = fps
        self.height = 2*(height//2) # some video_codecs require images with even size
        self.width = 2*(width//2)
        self.decimation = decimation
        self.video_profile = video_profile
        self.video_preset = video_preset
        self.video_quality = video_quality
        self.grayscale = grayscale

        if grayscale and (not video_codec in self.SUPPORTED_VIDEO_CODECS_GRAYSCALE):
            raise ValueError(f'wrong video_codec type for grayscale CPU encoding, supported video_codecs are: {self.SUPPORTED_VIDEO_CODECS_GRAYSCALE}') 
        
        if gpu and (not video_codec in self.SUPPORTED_VIDEO_CODECS_GPU):
            raise ValueError(f'wrong video_codec type for GPU encoding, supported video_codecs are: {self.SUPPORTED_VIDEO_CODECS_GPU}') 

        if (not gpu) and (not video_codec in self.SUPPORTED_VIDEO_CODECS_CPU):
            raise ValueError(f'wrong video_codec type for CPU encoding, supported video_codecs are: {self.SUPPORTED_VIDEO_CODECS_CPU}')
    
        self.video_codec = video_codec
        self.gpu = gpu
        self.writer = None

    def initialize(self) -> None:

        super().initialize()
        
        if self.gpu:
            self.writer = FFMPEG_VideoWriter_GPU_YUV420P(
                height = self.height, 
                width = self.width, 
                fps = self.fps, 
                q = self.video_quality,
                filename = self.video_filename,
                codec = self.video_codec,
                profile = self.video_profile,
                preset = self.video_preset
            )

        elif self.grayscale:
            self.writer = FFMPEG_VideoWriter_CPU_Grayscale(
                height = self.height, 
                width = self.width, 
                fps = self.fps, 
                q = self.video_quality,
                filename = self.video_filename,
                codec = self.video_codec,
                profile = self.video_profile,
                preset = self.video_preset
            )

        else:
            self.writer = FFMPEG_VideoWriter_CPU_YUV420P(
                height = self.height, 
                width = self.width, 
                fps = self.fps, 
                q = self.video_quality,
                filename = self.video_filename,
                codec = self.video_codec,
                profile = self.video_profile,
                preset = self.video_preset
            )

        self.fd = open(self.timings_filename, 'w')
        headers = ('index', 'timestamp', 'camera_timestamp')
        self.fd.write(','.join(headers) + '\n')

    def cleanup(self) -> None:

        super().cleanup()
        self.writer.close()
        self.fd.close()

    def process_data(self, data: NDArray) -> None:

        if data is None:
            return

        if data['index'] % self.decimation == 0:
            
            self.writer.write_frame(data['image'])
            self.fd.write(f"{data['index']}, {data['timestamp']}, {data['camera_timestamp']}\n")

            return data

    def process_metadata(self, metadata) -> Any:
        pass