from PyQt5.QtWidgets import (
    QWidget, 
    QApplication,
    QVBoxLayout, 
    QLabel,
)
from PyQt5.QtCore import pyqtSignal, Qt
from typing import Dict
from numpy.typing import NDArray
import numpy as np
import cv2
import os

from qt_widgets import (
    LabeledSpinBox, 
    NDarray_to_QPixmap
)
import numpy as np

class AssignmentWidget(QWidget):

    state_changed = pyqtSignal()
    PREVIEW_HEIGHT: int = 512
    DEFAULT_FILE = 'ZebVR/default/background.npy'

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if os.path.exists(self.DEFAULT_FILE):
            self.image = np.load(self.DEFAULT_FILE)
        else:
            self.image = np.zeros((512,512), dtype=np.uint8)
        self.ROIs = []

        self.declare_components()
        self.layout_components()

    def declare_components(self):

        self.row = LabeledSpinBox()
        self.row.setText('row')
        self.row.setRange(1,10)
        self.row.setSingleStep(1)
        self.row.setValue(1)
        self.row.valueChanged.connect(self.on_change)

        self.col = LabeledSpinBox()
        self.col.setText('col')
        self.col.setRange(1,10)
        self.col.setSingleStep(1)
        self.col.setValue(1)
        self.col.valueChanged.connect(self.on_change)

        self.width = LabeledSpinBox()
        self.width.setText('width')
        self.width.setRange(0,10_000)
        self.width.setSingleStep(1)
        self.width.setValue(self.image.shape[1])
        self.width.valueChanged.connect(self.on_change)

        self.height = LabeledSpinBox()
        self.height.setText('height')
        self.height.setRange(0,10_000)
        self.height.setSingleStep(1)
        self.height.setValue(self.image.shape[0])
        self.height.valueChanged.connect(self.on_change)
    
        self.offsetX = LabeledSpinBox()
        self.offsetX.setText('offsetX')
        self.offsetX.setRange(0,10_000)
        self.offsetX.setSingleStep(1)
        self.offsetX.setValue(0)
        self.offsetX.valueChanged.connect(self.on_change)

        self.offsetY = LabeledSpinBox()
        self.offsetY.setText('offsetY')
        self.offsetY.setRange(0,10_000)
        self.offsetY.setSingleStep(1)
        self.offsetY.setValue(0)
        self.offsetY.valueChanged.connect(self.on_change)

        self.image_label = QLabel()
        self.set_image(self.image)

    def layout_components(self):
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.row)
        main_layout.addWidget(self.col)
        main_layout.addWidget(self.width)
        main_layout.addWidget(self.height)
        main_layout.addWidget(self.offsetX)
        main_layout.addWidget(self.offsetY)
        main_layout.addWidget(self.image_label)

    def on_change(self):
        self.set_image(self.image)
        self.state_changed.emit()
    
    def set_image(self, image: NDArray):

        self.image = image
        self.ROIs = []

        # Create a copy to draw the grid
        grid_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        # Get grid parameters
        rows, cols = self.row.value(), self.col.value()
        box_width, box_height = self.width.value()//cols, self.height.value()//rows
        offset_x, offset_y = self.offsetX.value(), self.offsetY.value()

        # Draw grid
        for r in range(rows):
            for c in range(cols):
                x1 = min(offset_x + c * box_width, image.shape[1])
                y1 = min(offset_y + r * box_height, image.shape[0])
                x2 = min(x1 + box_width, image.shape[1]) 
                y2 = min(y1 + box_height, image.shape[0])
                color = (0, 255, 0) 
                thickness = 2
                cv2.rectangle(grid_image, (x1, y1), (x2, y2), color, thickness)
                self.ROIs.append((x1,y1,box_width,box_height))

        # Convert to QPixmap and display
        h, w = image.shape[:2]
        preview_width = int(w * self.PREVIEW_HEIGHT/h)
        image_resized = cv2.resize(grid_image,(preview_width, self.PREVIEW_HEIGHT), cv2.INTER_NEAREST)
        self.image_label.setPixmap(NDarray_to_QPixmap(image_resized))

    def get_state(self) -> Dict:

        state = {
            'row': self.row.value(),
            'col': self.col.value(),
            'width': self.width.value(),
            'height': self.height.value(),
            'offsetX': self.offsetX.value(),
            'offsetY': self.offsetY.value(),
            'ROIs': self.ROIs
        }
        return state
    
    def set_state(self, state: Dict) -> None:
        
        setters = {
            'row': self.row.setValue,
            'col': self.col.setValue,
            'width': self.width.setValue,
            'height': self.height.setValue,
            'offsetX': self.offsetX.setValue,
            'offsetY': self.offsetY.setValue,
        }

        for key, setter in setters.items():
            if key in state:
                setter(state[key])
        
if __name__ == "__main__":
    
    app = QApplication([])
    window = AssignmentWidget()
    window.show()
    app.exec()
