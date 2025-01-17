
from camera_tools import Camera
from image_tools import im2gray
from dagline import WorkerNode
import time
from typing import Callable, Any
import numpy as np

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
        self.offsetx = offsetx
        self.offsety = offsety
        self.updated = False
    
    def initialize(self) -> None:
        super().initialize()
        self.cam = self.camera_constructor()
        self.cam.set_exposure(self.exposure)
        self.cam.set_gain(self.gain)
        self.cam.set_framerate(self.framerate)
        self.cam.set_height(self.height)
        self.cam.set_width(self.width)
        self.cam.set_offsetX(self.offsetx)
        self.cam.set_offsetY(self.offsety)
        self.cam.start_acquisition()
        self.updated = True

    def cleanup(self) -> None:
        super().cleanup()
        self.cam.stop_acquisition()
    
    def process_data(self, data: None): 
        frame = self.cam.get_frame()
        
        if frame:

            img = frame['image']
            img_res = np.array(
                (frame['index'], time.perf_counter_ns(), img), # not using the timestamp from the camera
                dtype=np.dtype([
                    ('index', int),
                    ('timestamp', np.float64),
                    ('image', img.dtype, img.shape)
                ])
            )
            
            res = {}
            res['cam_output1'] = img_res
            res['cam_output2'] = img_res
            return res
        
    def process_metadata(self, metadata) -> Any:
        pass
