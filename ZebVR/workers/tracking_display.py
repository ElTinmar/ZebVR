from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional
import time
#import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication
from tracker import MultiFishOverlay
from image_tools import im2uint8
from geometry import Affine2DTransform
from ZebVR.widgets import DisplayWidget, TrackerType, DisplayType

class TrackingDisplay(WorkerNode):

    def __init__(
            self, 
            overlay: MultiFishOverlay,
            fps: int = 30,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.overlay = overlay
        self.fps = fps
        self.prev_time = 0
        self.first_timestamp = 0

    def initialize(self) -> None:

        super().initialize()
        
        self.app = QApplication([])
        self.window = DisplayWidget()
        self.window.show()

    def process_data(self, data) -> NDArray:
        self.app.processEvents()
        self.app.sendPostedEvents()
        
        if data is not None:

            if self.first_timestamp == 0:
                self.first_timestamp = data['timestamp']

            # restrict update freq to save resources
            if time.monotonic() - self.prev_time > 1/self.fps:

                if data['tracking']['animals']['identities'] is None:
                    return
            
                button_pressed = self.window.get_state()
                image_to_display = None
                
                try:
                    if button_pressed['display_type'] == DisplayType.RAW:

                        if button_pressed['tracker_type'] == TrackerType.MULTI:
                            image_to_display = im2uint8(data['tracking']['image'])

                        if button_pressed['tracker_type'] == TrackerType.ANIMAL:
                            image_to_display = im2uint8(data['tracking']['animals']['image'])

                        if button_pressed['tracker_type'] == TrackerType.BODY:
                            image_to_display = im2uint8(data['tracking']['body'][0]['image'])

                        if button_pressed['tracker_type'] == TrackerType.EYES:
                            image_to_display = im2uint8(data['tracking']['eyes'][0]['image'])

                        if button_pressed['tracker_type'] == TrackerType.TAIL:
                            image_to_display = im2uint8(data['tracking']['tail'][0]['image'])
                    
                    if button_pressed['display_type'] == DisplayType.OVERLAY:

                        if button_pressed['tracker_type'] == TrackerType.MULTI:
                            image_to_display = self.overlay.overlay(data['tracking']['image'], data['tracking'])

                        if button_pressed['tracker_type'] == TrackerType.ANIMAL:
                            s = data['tracking'].downsample_fullres_export
                            S = Affine2DTransform.scaling(s,s)
                            image_to_display = self.overlay.animal.overlay(data['tracking']['image'], data['tracking']['animals'], S)

                        if button_pressed['tracker_type'] == TrackerType.BODY:
                            image_to_display = self.overlay.body.overlay(data['tracking']['body'][0]['image_fullres'], data['tracking']['body'][0])

                        if button_pressed['tracker_type'] == TrackerType.EYES:
                            tx, ty = -data['tracking']['eyes'][0]['origin']
                            T = Affine2DTransform.translation(tx, ty)
                            image_to_display = self.overlay.eyes.overlay(data['tracking']['eyes'][0]['image_fullres'], data['tracking']['eyes'][0],T)

                        if button_pressed['tracker_type'] == TrackerType.TAIL:
                            tx, ty = -data['tracking']['tail'][0]['origin']
                            T = Affine2DTransform.translation(tx, ty)
                            image_to_display = self.overlay.tail.overlay(data['tracking']['tail'][0]['image_fullres'], data['tracking']['tail'][0],T)

                    if button_pressed['display_type'] == DisplayType.MASK:

                        if button_pressed['tracker_type'] == TrackerType.MULTI:
                            # there is no mask for multi, show image instead
                            image_to_display = im2uint8(data['tracking']['image'])

                        if button_pressed['tracker_type'] == TrackerType.ANIMAL:
                            image_to_display = im2uint8(data['tracking']['animals']['mask'])

                        if button_pressed['tracker_type'] == TrackerType.BODY:
                            image_to_display = im2uint8(data['tracking']['body'][0]['mask'])

                        if button_pressed['tracker_type'] == TrackerType.EYES:
                            image_to_display = im2uint8(data['tracking']['eyes'][0]['mask'])

                        if button_pressed['tracker_type'] == TrackerType.TAIL:
                            # there is no mask for the tail, show image instead
                            image_to_display = im2uint8(data['tracking']['tail'][0]['image'])
                except:
                    pass
               
                # update widget
                if image_to_display is not None:
                    self.window.set_state(
                        index=data['index'],
                        timestamp=round((data['timestamp'] - self.first_timestamp)*1e-9,3),
                        image=image_to_display
                    )

                self.prev_time = time.monotonic()

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        pass
        