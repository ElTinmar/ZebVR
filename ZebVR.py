from core.VR import VR
from devices.camera.dummycam import FromFile, RandomCam

cam_opts = {"ROI_height": 128, "ROI_width": 256}
camera = RandomCam(**cam_opts)

projector = 
background = 
cam2proj = 
tracker = 
stimulus = 

VirtualReality = VR(camera, projector, background, cam2proj, tracker, stimulus)