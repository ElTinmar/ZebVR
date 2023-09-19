from core.abstractclasses import CameraData, Camera
from core.dataclasses import CameraParameters
from typing import Tuple
from ximea import xiapi
from numpy.typing import NDArray

class XimeaImage(CameraData):
    def __init__(
            self, 
            pixeldata: NDArray, 
            index: int, 
            timestamp: float
        ) -> None:
        super().__init__()
        self.pixeldata = pixeldata
        self.index = index
        self.timestamp = timestamp
         
    def get_img(self) -> NDArray:
        """return image data"""
        return self.pixeldata

    def get_index(self) -> int:
        """return frame index"""
        return self.index
    
    def get_timestamp(self) -> float:
        """return timestamps in ns"""
        return self.timestamp
    
    def reallocate(self) -> None:
        """return buffer to camera"""
        pass

class XimeaCamera(Camera):
    def __init__(self, parameters: CameraParameters):
        super().__init__(parameters)
        self.xi_cam = None
        self.xi_img = None

    def configure(self):
        # open camera
        self.xi_cam = xiapi.Camera()
        self.xi_cam.open_device()
        
        # create buffer 
        self.xi_img = xiapi.Image()

        # configure camera TODO check that parameters are valid (ROI)
        self.xi_cam.set_exposure(self.parameters.exposure_time_ms)
        self.xi_cam.set_framerate(self.parameters.fps)
        self.xi_cam.set_gain(self.parameters.gain)
        self.xi_cam.set_width(self.parameters.ROI_width)
        self.xi_cam.set_height(self.parameters.ROI_height)
        self.xi_cam.set_offsetX(self.parameters.ROI_left)
        self.xi_cam.set_offsetY(self.parameters.ROI_top)

    def start_acquisition(self) -> None:
        self.configure()
        self.xi_cam.start_acquisition()
    
    def stop_acquisition(self) -> None:
        self.xi_cam.stop_acquisition()

    def fetch(self) -> Tuple[CameraData, bool]:
        try:
            self.xi_cam.get_image(self.xi_img)
            pixeldata = self.xi_img.get_image_data_numpy()
            im_num = self.xi_img.acq_nframe
            ts_sec = self.xi_img.tsSec
            ts_usec = self.xi_img.tsUSec
            timestamp =  (ts_sec*1_000_000 +  ts_usec)/1_000_000
            return (XimeaImage(pixeldata, im_num, timestamp), True)
        except:
            return (None, False)

    def __del__(self):
        if self.xi_cam is not None:
            self.xi_cam.close_device()