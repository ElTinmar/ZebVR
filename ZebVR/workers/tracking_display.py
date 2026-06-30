from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional
import time
#import pyqtgraph as pg
from qtpy.QtWidgets import QApplication
from tracker import SingleFishOverlay
from image_tools import im2uint8
from geometry import SimilarityTransform2D
from ..widgets import TrackingDisplayWidget, TrackerType, DisplayType, Summary
import numpy as np
import cv2

TRACKER_KEYS = {
    TrackerType.MULTI: 'animals',
    TrackerType.ANIMAL: 'animals',
    TrackerType.BODY: 'body',
    TrackerType.EYES: 'eyes',
    TrackerType.TAIL: 'tail'
}

OVERLAY_ATTRS = {
    TrackerType.ANIMAL: 'animal',
    TrackerType.BODY: 'body',
    TrackerType.EYES: 'eyes',
    TrackerType.TAIL: 'tail'
}

class TrackingDisplay(WorkerNode):

    def __init__(
            self, 
            overlay: SingleFishOverlay,
            n_animals: int = 1, 
            fps: int = 30,
            display_height: int = 512,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.overlay = overlay
        self.fps = fps
        self.n_animals = n_animals
        self.prev_time = 0
        self.first_timestamp = 0
        self.display_height = display_height

        # montage buffers
        self.n_cols = int(np.ceil(np.sqrt(n_animals)))
        self.n_rows = int(np.ceil(n_animals/self.n_cols))
        self.montage_buffer = {}
        for display in DisplayType:
            self.montage_buffer[display] = {}
            for tracker in TrackerType:
                self.montage_buffer[display][tracker] = np.zeros(
                    (self.n_rows*display_height, self.n_cols*display_height, 3), 
                    dtype=np.uint8
                )

    def _get_buffer(self, animal_id: int, display: DisplayType, tracker: TrackerType):
        buffer = self.montage_buffer[display][tracker]

        r = animal_id // self.n_cols
        c = animal_id % self.n_cols
        h = self.display_height

        row_start = r * h
        row_end = row_start + h
        col_start = c * h
        col_end = col_start + h

        return buffer[row_start:row_end, col_start:col_end, ...]

    def put_into_buffer(self, image_to_display: NDArray, buffer_view: NDArray) -> None:
        """
        Resizes image_to_display to fit inside the provided buffer_view slice,
        preserving its aspect ratio and centering it.
        """
        if image_to_display is None or image_to_display.size == 0:
            return

        # make sure we are working with uint8
        image_to_display = im2uint8(image_to_display)

        # clear previous content
        buffer_view.fill(0)

        if len(image_to_display.shape) == 2:
            image_rgb = cv2.cvtColor(image_to_display, cv2.COLOR_GRAY2RGB)
        else:
            image_rgb = image_to_display

        img_h, img_w = image_rgb.shape[:2]
        target_size = buffer_view.shape[0]  

        # Determine scale factor based on which dimension limits us first
        scale = min(target_size / img_h, target_size / img_w)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)

        if new_w == 0 or new_h == 0:
            return

        resized_img = cv2.resize(image_rgb, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
        pad_y = (target_size - new_h) // 2
        pad_x = (target_size - new_w) // 2

        buffer_view[pad_y:pad_y + new_h, pad_x:pad_x + new_w, ...] = resized_img

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
        fish_id = data['identity']
        display_type = state['display_type']
        tracker_type = state['tracker_type']
        summary_mode = state['summary_type'] 

        if summary_mode == Summary.INDIVIDUALS and fish_id != state['identity']:
            return

        buffer_view = self._get_buffer(fish_id, display_type, tracker_type)
            
        try:
            
            key = TRACKER_KEYS[tracker_type]
            tracking_data = data['tracking'][key]

            if display_type == DisplayType.PROCESSED:
                self.put_into_buffer(tracking_data['image_processed'], buffer_view)

            elif display_type == DisplayType.MASK:
                mask_key = 'mask' if tracker_type in [TrackerType.ANIMAL, TrackerType.BODY, TrackerType.EYES] else 'image_processed'
                self.put_into_buffer(tracking_data[mask_key], buffer_view)

            elif display_type == DisplayType.OVERLAY:
                if tracker_type == TrackerType.MULTI:
                    T_downsample = SimilarityTransform2D.scaling(tracking_data['downsample_ratio']) 
                    T_offset = SimilarityTransform2D.translation(-data['origin'][0], -data['origin'][1])
                    image_to_display = self.overlay.overlay_global(
                        tracking_data['image_downsampled'], 
                        data['tracking'],
                        T_downsample @ T_offset
                    )
                else:
                    attr_name = OVERLAY_ATTRS[tracker_type]
                    sub_overlay = getattr(self.overlay.overlay_param, attr_name)
                    image_to_display = sub_overlay.overlay_cropped(tracking_data)

                self.put_into_buffer(image_to_display, buffer_view)

        except:
            pass
        
        current_time = time.perf_counter()
        if current_time - self.prev_time > 1 / self.fps:

            if summary_mode == Summary.INDIVIDUALS:
                self.window.set_state(
                    index=data['index'],
                    timestamp=(data['timestamp'] - self.first_timestamp)*1e-9,
                    image=buffer_view
                )

            elif summary_mode == Summary.SUMMARY:
                self.window.set_state(
                    index=data['index'],
                    timestamp=(data['timestamp'] - self.first_timestamp)*1e-9,
                    image=self.montage_buffer[display_type][tracker_type]
                )

            self.prev_time = time.perf_counter()

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        pass
        