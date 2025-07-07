from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional
import time
#import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication
from tracker import SingleFishOverlay
from image_tools import im2uint8
from geometry import SimilarityTransform2D
from ..widgets import TrackingDisplayWidget, TrackerType, DisplayType

class TrackingDisplay(WorkerNode):

    def __init__(
            self, 
            overlay: SingleFishOverlay,
            n_animals: int = 1, 
            fps: int = 30,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.overlay = overlay
        self.fps = fps
        self.n_animals = n_animals
        self.prev_time = 0
        self.first_timestamp = 0

    def initialize(self) -> None:

        super().initialize()
        
        self.app = QApplication([])
        self.window = TrackingDisplayWidget(n_animals=self.n_animals)
        self.window.show()

    def process_data(self, data) -> NDArray:
        
        self.app.processEvents()
        self.app.sendPostedEvents()
        
        if data is None:
            return

        if self.first_timestamp == 0:
            self.first_timestamp = data['timestamp'].copy()

        state = self.window.get_state()

        if state['identity'] != data['identity']:
            return
            
        # restrict update freq to save resources
        if time.perf_counter() - self.prev_time > 1/self.fps:

            image_to_display = None
            
            try:
                if state['display_type'] == DisplayType.PROCESSED:

                    if state['tracker_type'] == TrackerType.MULTI:
                        image_to_display = im2uint8(data['tracking']['animals']['image_processed'])

                    if state['tracker_type'] == TrackerType.ANIMAL:
                        image_to_display = im2uint8(data['tracking']['animals']['image_processed'])

                    if state['tracker_type'] == TrackerType.BODY:
                        image_to_display = im2uint8(data['tracking']['body']['image_processed'])

                    if state['tracker_type'] == TrackerType.EYES:
                        image_to_display = im2uint8(data['tracking']['eyes']['image_processed'])

                    if state['tracker_type'] == TrackerType.TAIL:
                        image_to_display = im2uint8(data['tracking']['tail']['image_processed'])
                
                if state['display_type'] == DisplayType.OVERLAY:
                        
                    T_downsample = SimilarityTransform2D.scaling(
                        data['tracking']['animals']['downsample_ratio']
                    ) 

                    T_offset = SimilarityTransform2D.translation(-data['origin'][0], -data['origin'][1])

                    if state['tracker_type'] == TrackerType.MULTI:
                        image_to_display = self.overlay.overlay_global(
                            data['tracking']['animals']['image_downsampled'], 
                            data['tracking'],
                            T_downsample @ T_offset
                        )

                    if state['tracker_type'] == TrackerType.ANIMAL:
                        image_to_display = self.overlay.overlay_param.animal.overlay_cropped(
                            data['tracking']['animals']
                        )

                    if state['tracker_type'] == TrackerType.BODY:
                        image_to_display = self.overlay.overlay_param.body.overlay_cropped(
                            data['tracking']['body']
                        )

                    if state['tracker_type'] == TrackerType.EYES:
                        image_to_display = self.overlay.overlay_param.eyes.overlay_cropped(
                            data['tracking']['eyes']
                        )

                    if state['tracker_type'] == TrackerType.TAIL:
                        image_to_display = self.overlay.overlay_param.tail.overlay_cropped(
                            data['tracking']['tail']
                        )

                if state['display_type'] == DisplayType.MASK:

                    if state['tracker_type'] == TrackerType.MULTI:
                        # there is no mask for multi, show image instead
                        image_to_display = im2uint8(data['tracking']['animals']['image_processed'])

                    if state['tracker_type'] == TrackerType.ANIMAL:
                        image_to_display = im2uint8(data['tracking']['animals']['mask'])

                    if state['tracker_type'] == TrackerType.BODY:
                        image_to_display = im2uint8(data['tracking']['body']['mask'])

                    if state['tracker_type'] == TrackerType.EYES:
                        image_to_display = im2uint8(data['tracking']['eyes']['mask'])

                    if state['tracker_type'] == TrackerType.TAIL:
                        # there is no mask for the tail, show image instead
                        image_to_display = im2uint8(data['tracking']['tail']['image_processed'])
            except:
                pass
            
            # update widget
            if image_to_display is not None:
                self.window.set_state(
                    index=data['index'],
                    timestamp=(data['timestamp'] - self.first_timestamp)*1e-9,
                    image=image_to_display
                )

            self.prev_time = time.perf_counter()

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        pass
        