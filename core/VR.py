from core.abstractclasses import (
    Camera, Projector, Background, Cam2Proj, 
    Tracker, TrackerDisplay, Stimulus, ImageSaver
)
import cv2
import numpy as np
import time

polarity = -1

class VR:
    def __init__(
        self,
        camera: Camera, 
        projector: Projector,
        background: Background,
        cam2proj: Cam2Proj,
        tracker: Tracker,
        tracker_display: TrackerDisplay,
        stimulus: Stimulus,
        writer: ImageSaver = None
    ) -> None:
        
        self.camera = camera
        self.projector = projector
        self.background = background
        self.cam2proj = cam2proj
        self.tracker = tracker
        self.stimulus = stimulus
        self.tracker_display = tracker_display
        self.writer = writer

        #self.calibration()
        #self.registration()
        self.run()


    def calibration(self):
        self.camera.calibration()
        self.projector.calibration()

    def registration(self):
        self.cam2proj.registration()

    def run(self):

        cv2.namedWindow('VR')
        self.camera.start_acquisition()
        #self.writer.start()
        self.stimulus.init_window()

        camera_fetch_time = 0
        background_time = 0
        tracking_time = 0
        overlay_time = 0
        visual_stim_time = 0
        projector_time = 0
        loop_time = 0
        num_loops = 0

        keepgoing = True
        while keepgoing:
            start_time_ns = time.process_time_ns()
            data, keepgoing = self.camera.fetch()
            camera_fetch_time += (time.process_time_ns() - start_time_ns)

            if keepgoing:
                image = data.get_img()
                timestamp = data.get_timestamp()

                self.background.add_image(image)
                background_image = self.background.get_background() 
                back_sub = polarity*(image - background_image)
                background_time += (time.process_time_ns() - start_time_ns) 

                tracking = self.tracker.track(back_sub)
                tracking_time += (time.process_time_ns() - start_time_ns) 

                overlay = self.tracker_display.overlay(tracking, back_sub)
                for c in range(overlay.shape[2]):
                    overlay[:,:,c] = overlay[:,:,c] + image
                overlay = 255*overlay
                overlay[overlay>255]=255
                overlay = overlay.astype(np.uint8)
                overlay_time += (time.process_time_ns() - start_time_ns) 

                stim_image = self.stimulus.project(tracking)
                visual_stim_time += (time.process_time_ns() - start_time_ns) 

                #self.projector.project(stim_image)
                projector_time += (time.process_time_ns() - start_time_ns) 

                data.reallocate()
                
                cv2.imshow('VR', overlay)
                cv2.waitKey(1)
                
                #self.writer.write(overlay)

                num_loops+=1
                loop_time += (time.process_time_ns() - start_time_ns) 
            
        self.camera.stop_acquisition()
        #self.writer.stop()
        self.stimulus.close_window()
        cv2.destroyWindow('VR')

        print(f'camera_fetch_time {1e-9 * camera_fetch_time/num_loops} s per loop')
        print(f'background_time {1e-9 * background_time/num_loops} s per loop')
        print(f'tracking_time {1e-9 * tracking_time/num_loops} s per loop')
        print(f'overlay_time {1e-9 * overlay_time/num_loops} s per loop')
        print(f'visual_stim_time {1e-9 * visual_stim_time/num_loops} s per loop')
        print(f'projector_time {1e-9 * projector_time/num_loops} s per loop')
        print(f'loop_time {1e-9 * loop_time/num_loops} s per loop')
