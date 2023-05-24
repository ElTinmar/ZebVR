from core.VR import VR
from devices.camera.dummycam import FromFile, RandomCam
from core.abstractclasses import Projector

cam_opts = {"ROI_height": 128, "ROI_width": 256}
camera = RandomCam(**cam_opts)
projector = Projector(monitor_id = 1)
background = 
cam2proj = 
tracker = 
stimulus = 

VirtualReality = VR(camera, projector, background, cam2proj, tracker, stimulus)