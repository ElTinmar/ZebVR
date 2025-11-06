
from camera_tools import Camera
from dagline import WorkerNode
from typing import Callable, Any
import numpy as np
from numpy.typing import DTypeLike
from ZebVR.utils import get_time_ns
from image_tools import im2gray

class CameraWorker(WorkerNode):

    def __init__(
            self, 
            camera_constructor: Callable[[], Camera], 
            exposure: float,
            gain: float,
            framerate: float,
            height: int,
            width: int,
            offsetx: int,
            offsety: int,
            num_channels: int = 1,
            image_dtype: DTypeLike = np.uint8, 
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.camera_constructor = camera_constructor
        self.exposure = exposure
        self.gain = gain
        self.framerate = framerate
        self.height = height
        self.width = width
        self.num_channels = num_channels
        self.offsetx = offsetx
        self.offsety = offsety
        self.image_dtype = image_dtype

        if num_channels == 1:
            shape = (height, width)
        else:
            shape = (height, width, num_channels)

        # preallocate memory
        self.res = np.empty((),
            dtype=np.dtype([
                ('index', int),
                ('timestamp', np.int64),
                ('camera_timestamp', np.float64),
                ('image', image_dtype, shape)
            ])
        )
    
    def initialize(self) -> None:
        super().initialize()
        self.cam = self.camera_constructor()
        self.cam.set_width(self.width)
        self.cam.set_height(self.height)
        self.cam.set_framerate(self.framerate)
        self.cam.set_offsetX(self.offsetx)
        self.cam.set_offsetY(self.offsety)
        self.cam.set_exposure(self.exposure)
        self.cam.set_gain(self.gain)
        print({
            'width': self.cam.get_width(),
            'height': self.cam.get_height(),
            'framerate': self.cam.get_framerate(),
            'offsetX': self.cam.get_offsetX(),
            'offsetY': self.cam.get_offsetY(),
            'exposure': self.cam.get_exposure(),
            'gain': self.cam.get_gain(),
        })
        self.cam.start_acquisition()

    def cleanup(self) -> None:
        super().cleanup()
        self.cam.stop_acquisition()
    
    def process_data(self, data: None): 

        frame = self.cam.get_frame()
        timestamp = get_time_ns()
        
        if frame:
            self.res['index'] = frame['index']
            self.res['timestamp'] = timestamp
            self.res['camera_timestamp'] = frame['timestamp']
            self.res['image'] = frame['image']

            res = {}
            res['cam_output1'] = self.res
            res['cam_output2'] = self.res
            return res
        
    def process_metadata(self, metadata) -> Any:
        pass
