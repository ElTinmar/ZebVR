
from camera_tools import Camera
from image_tools import im2gray
from dagline import WorkerNode
import time
from typing import Callable, Any

class CameraWorker(WorkerNode):

    def __init__(
            self, 
            camera_constructor: Callable[[Camera], None], 
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
            img = im2gray(frame.image)
            res = {}
            res['background_subtraction'] = (frame.index, time.perf_counter_ns(), img)
            res['image_saver'] = (frame.index, time.perf_counter_ns(), img)
            return res
        
    def process_metadata(self, metadata) -> Any:
        # receive
        control = metadata['camera_control']
        if control is not None: 
            self.cam.stop_acquisition()
            self.cam.set_exposure(control['exposure'])
            self.cam.set_gain(control['gain'])
            self.cam.set_framerate(control['framerate'])
            self.cam.start_acquisition()
            self.updated = True
        
        # send
        # if camera settings were updated, send info
        if self.updated:
            self.updated = False
            # TODO make sure all cameras support these functions and reply something coherent
            try:
                res = {}
                res['camera_info'] = {}
                res['camera_info']['exposure'] = {}
                res['camera_info']['gain'] = {}
                res['camera_info']['framerate'] = {}
                res['camera_info']['exposure']['value'] = self.cam.get_exposure()
                res['camera_info']['exposure']['min'], res['camera_info']['exposure']['max'] = self.cam.get_exposure_range()
                res['camera_info']['exposure']['increment'] = self.cam.get_exposure_increment()
                res['camera_info']['gain']['value'] = self.cam.get_gain()
                res['camera_info']['gain']['min'], res['camera_info']['gain']['max'] = self.cam.get_gain_range()
                res['camera_info']['gain']['increment'] = self.cam.get_gain_increment()
                res['camera_info']['framerate']['value'] = self.cam.get_framerate()
                res['camera_info']['framerate']['min'], res['camera_info']['framerate']['max'] = self.cam.get_framerate_range()
                res['camera_info']['framerate']['increment'] = self.cam.get_framerate_increment()
                return res
            except:
                pass