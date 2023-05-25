from .protocols import Camera, Projector, Background, Cam2Proj, Tracker, Stimulus
import cv2
from tracking.utils.im2gray import im2gray
from tracking.utils.im2float import im2single

class VR:
    def __init__(
        self,
        camera: Camera, 
        projector: Projector,
        background: Background,
        cam2proj: Cam2Proj,
        tracker: Tracker,
        stimulus: Stimulus
    ) -> None:
        
        self.camera = camera
        self.projector = projector
        self.background = background
        self.cam2proj = cam2proj
        self.tracker = tracker
        self.stimulus = stimulus

        self.calibration()
        self.registration()
        self.run()


    def calibration(self):
        self.camera.calibration()
        self.projector.calibration()

    def registration(self):
        self.cam2proj.registration()

    def run(self):

        cv2.namedWindow('VR')
        self.camera.start_acquisition()

        keepgoing = True
        while keepgoing:
            data, keepgoing = self.camera.fetch()
            if keepgoing:
                image = data.get_img()
                self.background.add_image(image)
                background_image = self.background.get_background() 
                back_sub = abs(image - background_image)
                tracking = self.tracker.track(back_sub)
                overlay = self.tracker.tracking_overlay(back_sub)
                stim_image = self.stimulus.create_stim_image(tracking)
                self.projector.project(stim_image)
                data.reallocate()
                
                for c in range(overlay.shape[2]):
                    overlay[:,:,c] = overlay[:,:,c] + image

                cv2.imshow('VR', overlay)
                cv2.waitKey(1)

        self.camera.stop_acquisition()
        cv2.destroyWindow('VR')