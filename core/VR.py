from .protocols import Camera, Projector, Background, Cam2Proj, Tracker, Stimulus
class VR:
    def __init__(
        self,
        camera: Camera, 
        projector: Projector,
        background: Background,
        cam2proj: Cam2Proj,
        tracker: Tracker,
        stimulus: Stimulus,
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
        keepgoing = True
        while keepgoing:
            image, keepgoing = self.camera.get_image()
            if keepgoing:
                self.background.add_image(image)
                background_image = self.background.get_background() 
                tracking = self.tracker.track(image-background_image)
                stim_image = self.stimulus.create_stim_image(tracking)
                self.projector.project(stim_image)
