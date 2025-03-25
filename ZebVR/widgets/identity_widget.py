from PyQt5.QtWidgets import (
    QWidget, 
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGroupBox
)
from PyQt5.QtCore import pyqtSignal
from typing import Dict
from numpy.typing import NDArray
import numpy as np
import cv2
import os
from geometry import SimilarityTransform2D

from qt_widgets import (
    LabeledSpinBox, 
    LabeledDoubleSpinBox,
    NDarray_to_QPixmap
)
import numpy as np

class IdentityWidget(QWidget):

    state_changed = pyqtSignal()
    PREVIEW_HEIGHT: int = 512
    DEFAULT_FILE = 'ZebVR/default/background.npy'

    font = cv2.FONT_HERSHEY_SIMPLEX
    fontweight = 2
    fontsize = 1.5
    color = (0, 255, 0) 
    line_thickness = 2
    axis_y_color = (0, 0, 255)
    axis_x_color = (0, 255, 255) 

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if os.path.exists(self.DEFAULT_FILE):
            self.image = np.load(self.DEFAULT_FILE)
        else:
            self.image = np.zeros((512,512), dtype=np.uint8)
        self.ROIs = []
        self.open_loop_visible = False
        self.axes = [[1.0, 0.0], [0.0, 1.0]] 

        self.declare_components()
        self.layout_components()

    def declare_components(self) -> None:

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
        self.width.setRange(1,self.image.shape[1])
        self.width.setSingleStep(1)
        self.width.setValue(self.image.shape[1])
        self.width.valueChanged.connect(self.on_change)

        self.height = LabeledSpinBox()
        self.height.setText('height')
        self.height.setRange(1,self.image.shape[0])
        self.height.setSingleStep(1)
        self.height.setValue(self.image.shape[0])
        self.height.valueChanged.connect(self.on_change)
    
        self.offsetX = LabeledSpinBox()
        self.offsetX.setText('offsetX')
        self.offsetX.setRange(0,self.image.shape[1]-1)
        self.offsetX.setSingleStep(1)
        self.offsetX.setValue(0)
        self.offsetX.valueChanged.connect(self.on_change)

        self.offsetY = LabeledSpinBox()
        self.offsetY.setText('offsetY')
        self.offsetY.setRange(0,self.image.shape[0]-1)
        self.offsetY.setSingleStep(1)
        self.offsetY.setValue(0)
        self.offsetY.valueChanged.connect(self.on_change)

        self.marginX = LabeledSpinBox()
        self.marginX.setText('marginX')
        self.marginX.setRange(0,self.image.shape[1]-1)
        self.marginX.setSingleStep(1)
        self.marginX.setValue(0)
        self.marginX.valueChanged.connect(self.on_change)

        self.marginY = LabeledSpinBox()
        self.marginY.setText('marginY')
        self.marginY.setRange(0,self.image.shape[0]-1)
        self.marginY.setSingleStep(1)
        self.marginY.setValue(0)
        self.marginY.valueChanged.connect(self.on_change)

        self.centroid_X = LabeledSpinBox()
        self.centroid_X.setText('open-loop centroid offset X')
        self.centroid_X.setRange(0,self.image.shape[1]-1)
        self.centroid_X.setSingleStep(1)
        self.centroid_X.setValue(0)
        self.centroid_X.valueChanged.connect(self.on_change)

        self.centroid_Y = LabeledSpinBox()
        self.centroid_Y.setText('open-loop centroid offset Y')
        self.centroid_Y.setRange(0,self.image.shape[0]-1)
        self.centroid_Y.setSingleStep(1)
        self.centroid_Y.setValue(0)
        self.centroid_Y.valueChanged.connect(self.on_change)

        self.open_loop_group = QGroupBox('Open-loop coordinate system')

        self.rotation = LabeledDoubleSpinBox()
        self.rotation.setText(u'axes rotation (\N{DEGREE SIGN})')
        self.rotation.setRange(0,360)
        self.rotation.setSingleStep(0.5)
        self.rotation.setValue(0)
        self.rotation.valueChanged.connect(self.on_change)

        self.image_label = QLabel()
        self.set_image(self.image)

    def layout_components(self) -> None:

        image_layout = QHBoxLayout()
        image_layout.addStretch()
        image_layout.addWidget(self.image_label)
        image_layout.addStretch() 

        grid_layout = QHBoxLayout()
        grid_layout.addWidget(self.col)
        grid_layout.addWidget(self.row)
        grid_layout.setSpacing(50)

        size_layout = QHBoxLayout()
        size_layout.addWidget(self.width)
        size_layout.addWidget(self.height)
        size_layout.setSpacing(50)

        offset_layout = QHBoxLayout()
        offset_layout.addWidget(self.offsetX)
        offset_layout.addWidget(self.offsetY)
        offset_layout.setSpacing(50)

        margin_layout = QHBoxLayout()
        margin_layout.addWidget(self.marginX)
        margin_layout.addWidget(self.marginY)
        margin_layout.setSpacing(50)

        centroid_offset_layout = QHBoxLayout()
        centroid_offset_layout.addWidget(self.centroid_X)
        centroid_offset_layout.addWidget(self.centroid_Y)
        centroid_offset_layout.setSpacing(50)

        open_loop_layout = QVBoxLayout()
        open_loop_layout.addLayout(centroid_offset_layout)
        open_loop_layout.addWidget(self.rotation)
        self.open_loop_group.setLayout(open_loop_layout)
        
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(grid_layout)
        main_layout.addLayout(size_layout)
        main_layout.addLayout(offset_layout)
        main_layout.addLayout(margin_layout)
        main_layout.addStretch()
        main_layout.addWidget(self.open_loop_group)
        main_layout.addStretch()
        main_layout.addLayout(image_layout)
        main_layout.addStretch()

    def on_change(self) -> None:
        
        self.set_image(self.image)
        self.state_changed.emit()
    
    def set_image(self, image: NDArray) -> None:

        self.image = image

        self.ROIs.clear()
        self.width.setRange(1,self.image.shape[1])
        self.height.setRange(1,self.image.shape[0])
        self.offsetX.setRange(0,self.image.shape[1]-1)
        self.offsetY.setRange(0,self.image.shape[0]-1)

        # Create a copy to draw the grid
        grid_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        # Get grid parameters
        rows, cols = self.row.value(), self.col.value()
        offset_x, offset_y = self.offsetX.value(), self.offsetY.value()
        margin_x, margin_y = self.marginX.value(), self.marginY.value()
        box_width, box_height = (self.width.value() - 2*cols*margin_x)//cols, (self.height.value() - 2*rows*margin_y)//rows
        
        self.centroid_X.setRange(int(-box_width//2),int(box_width//2))
        self.centroid_Y.setRange(int(-box_height//2),int(box_height//2))
        
        self.axes = SimilarityTransform2D.rotation(np.deg2rad(self.rotation.value()))[:2,:2]
        centroid_offset_x = self.centroid_X.value()
        centroid_offset_y = self.centroid_Y.value()

        # Draw grid
        count = 0
        for r in range(rows):
            for c in range(cols):
                x1 = min(offset_x + c * (2*margin_x + box_width), image.shape[1])
                y1 = min(offset_y + r * (2*margin_y + box_height), image.shape[0])
                x2 = min(x1 + box_width, image.shape[1]) 
                y2 = min(y1 + box_height, image.shape[0])
                text = str(count)
                textsize = cv2.getTextSize(text, self.font, self.fontsize, self.fontweight)[0]
                centroid_x = x1+box_width//2
                centroid_y = y1+box_height//2
                scale_x = box_width//8
                scale_y = box_height//4
                
                cv2.rectangle(
                    grid_image, 
                    (x1, y1), (x2, y2), 
                    self.color, 
                    self.line_thickness
                )
                cv2.putText(
                    grid_image, 
                    str(count), 
                    (centroid_x-textsize[0]//2, centroid_y+textsize[1]//2), 
                    self.font, self.fontsize, 
                    self.color, 
                    self.fontweight, 
                    cv2.LINE_AA
                )

                if self.open_loop_visible:
                    cv2.line(
                        grid_image, 
                        (int(centroid_x+centroid_offset_x), int(centroid_y+centroid_offset_y)), 
                        (int(centroid_x+centroid_offset_x+scale_y*self.axes[0,1]), int(centroid_y+centroid_offset_y+scale_y*self.axes[1,1])), 
                        self.axis_y_color, 
                        self.line_thickness
                    )
                    cv2.line(
                        grid_image, 
                        (int(centroid_x+centroid_offset_x), int(centroid_y+centroid_offset_y)), 
                        (int(centroid_x+centroid_offset_x+scale_x*self.axes[0,0]), int(centroid_y+centroid_offset_y+scale_x*self.axes[1,0])), 
                        self.axis_x_color, 
                        self.line_thickness
                    )

                self.ROIs.append((x1,y1,x2-x1,y2-y1))
                count += 1

        # Convert to QPixmap and display
        h, w = image.shape[:2]
        preview_width = int(w * self.PREVIEW_HEIGHT/h)
        image_resized = cv2.resize(grid_image,(preview_width, self.PREVIEW_HEIGHT), cv2.INTER_NEAREST)
        self.image_label.setPixmap(NDarray_to_QPixmap(image_resized))

    def set_open_loop_visible(self, visible: bool) -> None:
        self.open_loop_group.setVisible(visible)
        self.open_loop_visible = visible
        self.on_change()

    def get_state(self) -> Dict:

        state = {
            'row': self.row.value(),
            'col': self.col.value(),
            'width': self.width.value(),
            'height': self.height.value(),
            'offsetX': self.offsetX.value(),
            'offsetY': self.offsetY.value(),
            'marginX': self.marginX.value(),
            'marginY': self.marginY.value(),
            'ROIs': self.ROIs,
            'n_animals': len(self.ROIs),
            'open_loop_x_offset': self.centroid_X.value(),
            'open_loop_y_offset': self.centroid_X.value(),
            'open_loop_axes': self.axes
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
            'marginX': self.marginX.setValue,
            'marginY': self.marginY.setValue,
            'open_loop_x_offset':  self.centroid_X.setValue,
            'open_loop_y_offset':  self.centroid_Y.setValue,
        }

        for key, setter in setters.items():
            if key in state:
                setter(state[key])

        self.axes = state.get('axes', [[1.0, 0.0], [0.0, 1.0]])
        
if __name__ == "__main__":
    
    app = QApplication([])
    window = IdentityWidget()
    window.show()
    app.exec()
