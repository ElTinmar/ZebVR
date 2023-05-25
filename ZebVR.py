from core.VR import VR
from devices.camera.dummycam import FromFile, RandomCam
from core.abstractclasses import Projector, Background

cam_opts = {"ROI_height": 128, "ROI_width": 256}
camera = RandomCam(**cam_opts)
projector = Projector(monitor_id = 1)
background = Background(num_images = 500, every_n_image = 100)
cam2proj = 
tracker = 
stimulus = 

VirtualReality = VR(camera, projector, background, cam2proj, tracker, stimulus)