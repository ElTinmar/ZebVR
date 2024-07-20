from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional
import time
from enum import Enum
#import pyqtgraph as pg

from PyQt5.QtWidgets import (
    QApplication, 
    QWidget, 
    QPushButton,
    QButtonGroup,
    QHBoxLayout,
    QVBoxLayout,
    QLabel
)

from tracker import MultiFishOverlay
from qt_widgets import NDarray_to_QPixmap, LabeledSpinBox
from image_tools import im2uint8

class TrackerType(Enum):
    MULTI: int = 0
    ANIMAL: int = 1
    BODY: int = 2
    EYES: int = 3
    TAIL: int = 4

class DisplayType(Enum):
    RAW: int = 0
    OVERLAY: int = 1
    MASK: int = 2

# TODO: add a widget to select fish num
# TODO: maybe add image histogram? Not sure about that though

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

    def initialize(self) -> None:

        super().initialize()
        
        self.updated = False
        self.app = QApplication([])
        self.window = QWidget()
        self.declare_components()
        self.layout_components()
        self.window.setWindowTitle('Tracking display')
        self.window.show()

    def declare_components(self):
        
        self.lbl_image = QLabel()

        self.lbl_index = QLabel()
        self.lbl_timestamp = QLabel()

        # TODO add widget to select which fish to show
        # and / or mouse click event

        self.btn_multi = QPushButton('multi')
        self.btn_multi.setCheckable(True)
        
        self.btn_animal = QPushButton('animals')
        self.btn_animal.setCheckable(True)

        self.btn_body = QPushButton('body')
        self.btn_body.setCheckable(True)

        self.btn_eyes = QPushButton('eyes')
        self.btn_eyes.setCheckable(True)

        self.btn_tail = QPushButton('tail')
        self.btn_tail.setCheckable(True)

        self.bg_tracker_type = QButtonGroup()
        self.bg_tracker_type.addButton(self.btn_multi, id=TrackerType.MULTI.value)
        self.bg_tracker_type.addButton(self.btn_animal, id=TrackerType.ANIMAL.value)
        self.bg_tracker_type.addButton(self.btn_body, id=TrackerType.BODY.value)
        self.bg_tracker_type.addButton(self.btn_eyes, id=TrackerType.EYES.value)
        self.bg_tracker_type.addButton(self.btn_tail, id=TrackerType.TAIL.value)
        self.btn_multi.setChecked(True)

        self.btn_raw = QPushButton('raw')
        self.btn_raw.setCheckable(True)

        self.btn_overlay = QPushButton('overlay')
        self.btn_overlay.setCheckable(True)

        self.btn_mask = QPushButton('mask')
        self.btn_mask.setCheckable(True)

        self.bg_display_type = QButtonGroup()
        self.bg_display_type.addButton(self.btn_raw, id=DisplayType.RAW.value)
        self.bg_display_type.addButton(self.btn_overlay, id=DisplayType.OVERLAY.value)
        self.bg_display_type.addButton(self.btn_mask, id=DisplayType.MASK.value)
        self.btn_raw.setChecked(True)

    def layout_components(self):

        layout_tracker_btn = QHBoxLayout()
        layout_tracker_btn.addWidget(self.btn_multi)
        layout_tracker_btn.addWidget(self.btn_animal)
        layout_tracker_btn.addWidget(self.btn_body)
        layout_tracker_btn.addWidget(self.btn_eyes)
        layout_tracker_btn.addWidget(self.btn_tail)

        layout_display_btn = QHBoxLayout()
        layout_display_btn.addWidget(self.btn_raw)
        layout_display_btn.addWidget(self.btn_overlay)
        layout_display_btn.addWidget(self.btn_mask)

        layout_status = QHBoxLayout()
        layout_status.addWidget(QLabel('index:'))
        layout_status.addWidget(self.lbl_index)
        layout_status.addStretch()
        layout_status.addWidget(QLabel('timestamp:'))
        layout_status.addWidget(self.lbl_timestamp)

        layout = QVBoxLayout(self.window)
        layout.addLayout(layout_tracker_btn)
        layout.addLayout(layout_display_btn)
        layout.addWidget(self.lbl_image)
        layout.addLayout(layout_status)

    def process_data(self, data) -> NDArray:
        self.app.processEvents()
        
        if data is not None:
            index, timestamp, tracking = data

            # restrict update freq to save resources
            if time.monotonic() - self.prev_time > 1/self.fps:

                if tracking.animals.identities is None:
                    return
            
                image_to_display = None

                if self.bg_display_type.checkedId() == DisplayType.RAW.value:

                    if self.bg_tracker_type.checkedId() == TrackerType.MULTI.value:
                        image_to_display = im2uint8(tracking.image)

                    if self.bg_tracker_type.checkedId() == TrackerType.ANIMAL.value:
                        image_to_display = im2uint8(tracking.animals.image)

                    if self.bg_tracker_type.checkedId() == TrackerType.BODY.value:
                        if tracking.body is None:
                            return
                        image_to_display = im2uint8(tracking.body[0].image)

                    if self.bg_tracker_type.checkedId() == TrackerType.EYES.value:
                        if tracking.eyes is None:
                            return
                        image_to_display = im2uint8(tracking.eyes[0].image)

                    if self.bg_tracker_type.checkedId() == TrackerType.TAIL.value:
                        if tracking.tail is None:
                            return
                        image_to_display = im2uint8(tracking.tail[0].image)
                
                if self.bg_display_type.checkedId() == DisplayType.OVERLAY.value:

                    if self.bg_tracker_type.checkedId() == TrackerType.MULTI.value:
                        image_to_display = self.overlay.overlay(tracking.image, tracking)

                    if self.bg_tracker_type.checkedId() == TrackerType.ANIMAL.value:
                        image_to_display = self.overlay.animal.overlay(tracking.animals.image, tracking.animals)

                    if self.bg_tracker_type.checkedId() == TrackerType.BODY.value:
                        if self.overlay.body is None:
                            return 
                        image_to_display = self.overlay.body.overlay(tracking.body[0].image, tracking.body[0])

                    if self.bg_tracker_type.checkedId() == TrackerType.EYES.value:
                        if self.overlay.eyes is None:
                            return
                        image_to_display = self.overlay.eyes.overlay(tracking.eyes[0].image, tracking.eyes[0])

                    if self.bg_tracker_type.checkedId() == TrackerType.TAIL.value:
                        if self.overlay.tail is None:
                            return
                        image_to_display = self.overlay.tail.overlay(tracking.tail[0].image, tracking.tail[0])

                if self.bg_display_type.checkedId() == DisplayType.MASK.value:

                    if self.bg_tracker_type.checkedId() == TrackerType.MULTI.value:
                        # there is no mask for multi, show image instead
                        image_to_display = im2uint8(tracking.image)

                    if self.bg_tracker_type.checkedId() == TrackerType.ANIMAL.value:
                        image_to_display = im2uint8(tracking.animals.mask)

                    if self.bg_tracker_type.checkedId() == TrackerType.BODY.value:
                        if tracking.body is None:
                            return
                        image_to_display = im2uint8(tracking.body[0].mask)

                    if self.bg_tracker_type.checkedId() == TrackerType.EYES.value:
                        if tracking.eyes is None:
                            return
                        image_to_display = im2uint8(tracking.eyes[0].mask)

                    if self.bg_tracker_type.checkedId() == TrackerType.TAIL.value:
                        # there is no mask for the tail, show image instead
                        if tracking.tail is None:
                            return
                        image_to_display = im2uint8(tracking.tail[0].image)
               
                # update labels
                if image_to_display is not None:
                    pixmap = NDarray_to_QPixmap(image_to_display)
                    self.lbl_image.setPixmap(pixmap)
                    self.lbl_index.setText(f'{index}')
                    self.lbl_timestamp.setText(f'{timestamp}')
                    self.window.update() # is this necessary?

                self.prev_time = time.monotonic()

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        pass
        