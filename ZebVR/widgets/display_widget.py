from enum import IntEnum
import cv2
from typing import Dict

#import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QWidget, 
    QPushButton,
    QButtonGroup,
    QHBoxLayout,
    QVBoxLayout,
    QLabel
)
from PyQt5.QtGui import QImage
from qt_widgets import NDarray_to_QPixmap, LabeledSpinBox

class TrackerType(IntEnum):
    MULTI = 0
    ANIMAL = 1
    BODY = 2
    EYES = 3
    TAIL = 4

class DisplayType(IntEnum):
    PROCESSED = 0
    OVERLAY = 1
    MASK = 2

# TODO: add a widget to select fish num
# TODO: maybe add image histogram? Not sure about that though

class DisplayWidget(QWidget):

    def __init__(
            self,
            display_height: int = 512,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)

        self.display_height = display_height 
        self.declare_components()
        self.layout_components()
        self.setWindowTitle('Display')
        self.show()

    def declare_components(self) -> None:

        self.lbl_index = QLabel()
        self.lbl_timestamp = QLabel()        
        self.lbl_image = QLabel()

    def layout_components(self) -> None:

        layout_status = QHBoxLayout()
        layout_status.addWidget(QLabel('index:'))
        layout_status.addWidget(self.lbl_index)
        layout_status.addStretch()
        layout_status.addWidget(QLabel('timestamp:'))
        layout_status.addWidget(self.lbl_timestamp)

        layout_image = QHBoxLayout()
        layout_image.addStretch()
        layout_image.addWidget(self.lbl_image)
        layout_image.addStretch() 

        layout = QVBoxLayout(self)
        layout.addLayout(layout_image)
        layout.addLayout(layout_status)

    def set_state(self, index, timestamp, image_rgb) -> None:

        # TODO make that an argument or controlled by a widget?    
        width = int(image_rgb.shape[1] * self.display_height/image_rgb.shape[0])
        image_resized = cv2.resize(image_rgb, (width, self.display_height), interpolation=cv2.INTER_NEAREST)

        pixmap = NDarray_to_QPixmap(image_resized, format = QImage.Format_RGB888)
        self.lbl_image.setPixmap(pixmap)
        self.lbl_index.setText(f'{index}')
        self.lbl_timestamp.setText(f'{timestamp:.03f}')
        self.update()

# TODO maybe rewrite this to inherit from DisplayWidget 
# to remove duplicate code
class TrackingDisplayWidget(QWidget):

    def __init__(
            self,
            display_height: int = 512,
            n_animals: int = 1,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)

        self.display_height = display_height 
        self.n_animals = n_animals
        self.declare_components()
        self.layout_components()
        self.setWindowTitle('Tracking display')
        self.show()

    def declare_components(self) -> None:

        self.animal_identity = LabeledSpinBox()
        self.animal_identity.setText('#animal')
        self.animal_identity.setRange(0,self.n_animals-1)
        self.animal_identity.setSingleStep(1)
        self.animal_identity.setValue(0)

        self.lbl_index = QLabel()
        self.lbl_timestamp = QLabel()        
        self.lbl_image = QLabel()

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
        self.bg_tracker_type.addButton(self.btn_multi, id=TrackerType.MULTI)
        self.bg_tracker_type.addButton(self.btn_animal, id=TrackerType.ANIMAL)
        self.bg_tracker_type.addButton(self.btn_body, id=TrackerType.BODY)
        self.bg_tracker_type.addButton(self.btn_eyes, id=TrackerType.EYES)
        self.bg_tracker_type.addButton(self.btn_tail, id=TrackerType.TAIL)
        self.btn_multi.setChecked(True)

        self.btn_processed = QPushButton('processed')
        self.btn_processed.setCheckable(True)

        self.btn_overlay = QPushButton('overlay')
        self.btn_overlay.setCheckable(True)

        self.btn_mask = QPushButton('mask')
        self.btn_mask.setCheckable(True)

        self.bg_display_type = QButtonGroup()
        self.bg_display_type.addButton(self.btn_processed, id=DisplayType.PROCESSED)
        self.bg_display_type.addButton(self.btn_overlay, id=DisplayType.OVERLAY)
        self.bg_display_type.addButton(self.btn_mask, id=DisplayType.MASK)
        self.btn_processed.setChecked(True)

    def layout_components(self) -> None:

        layout_tracker_btn = QHBoxLayout()
        layout_tracker_btn.addWidget(self.btn_multi)
        layout_tracker_btn.addWidget(self.btn_animal)
        layout_tracker_btn.addWidget(self.btn_body)
        layout_tracker_btn.addWidget(self.btn_eyes)
        layout_tracker_btn.addWidget(self.btn_tail)

        layout_display_btn = QHBoxLayout()
        layout_display_btn.addWidget(self.btn_processed)
        layout_display_btn.addWidget(self.btn_overlay)
        layout_display_btn.addWidget(self.btn_mask)

        layout_status = QHBoxLayout()
        layout_status.addWidget(QLabel('index:'))
        layout_status.addWidget(self.lbl_index)
        layout_status.addStretch()
        layout_status.addWidget(QLabel('timestamp:'))
        layout_status.addWidget(self.lbl_timestamp)

        layout_image = QHBoxLayout()
        layout_image.addStretch()
        layout_image.addWidget(self.lbl_image)
        layout_image.addStretch() 

        layout = QVBoxLayout(self)
        layout.addWidget(self.animal_identity)
        layout.addLayout(layout_tracker_btn)
        layout.addLayout(layout_display_btn)
        layout.addLayout(layout_image)
        layout.addLayout(layout_status)

    def get_state(self) -> Dict:
        state = {}
        state['identity'] = self.animal_identity.value()
        state['display_type'] = self.bg_display_type.checkedId()
        state['tracker_type'] = self.bg_tracker_type.checkedId()
        return state

    def set_state(self, index, timestamp, image) -> None:

        # TODO make that an argument or controlled by a widget?    
        width = int(image.shape[1] * self.display_height/image.shape[0])
        image_resized = cv2.resize(image, (width, self.display_height), interpolation=cv2.INTER_NEAREST)

        pixmap = NDarray_to_QPixmap(image_resized)
        self.lbl_image.setPixmap(pixmap)
        self.lbl_index.setText(f'{index}')
        self.lbl_timestamp.setText(f'{timestamp:.03f}')
        self.update()
