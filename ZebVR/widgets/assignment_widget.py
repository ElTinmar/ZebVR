from PyQt5.QtWidgets import (
    QWidget, 
    QApplication,
    QVBoxLayout, 
    QHBoxLayout, 
    QPushButton, 
    QLabel,
    QStackedWidget
)
from PyQt5.QtCore import pyqtSignal, Qt
from typing import Dict
from numpy.typing import NDArray
import numpy as np
import cv2
import os

from qt_widgets import (
    LabeledDoubleSpinBox, 
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
        self.declare_components()
        self.layout_components()

    def declare_components(self):

        self.rows = LabeledSpinBox()
        self.rows.setText('#animals')
        self.rows.setRange(0,100)
        self.rows.setSingleStep(1)
        self.rows.setValue(1)
        self.rows.valueChanged.connect(self.state_changed)

        self.image = QLabel()
        if os.path.exists(self.DEFAULT_FILE):
            self.set_image(np.load(self.DEFAULT_FILE))
        else:
            self.set_image(np.zeros((512,512), dtype=np.uint8))
        

    def layout_components(self):
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.self.image)
    
    def set_image(self, image: NDArray):
        # TODO maybe check that image is uint8
        h, w = image.shape[:2]
        preview_width = int(w * self.PREVIEW_HEIGHT/h)
        image_resized = cv2.resize(image,(preview_width, self.PREVIEW_HEIGHT), cv2.INTER_NEAREST)
        self.image.setPixmap(NDarray_to_QPixmap(image_resized))

    def get_state(self) -> Dict:
        state = {}
        return state
    
    def set_state(self, state: Dict) -> None:
        
        setters = {}

        for key, setter in setters.items():
            if key in state:
                setter(state[key])

if __name__ == "__main__":
    
    app = QApplication([])
    window = AssignmentWidget()
    window.show()
    app.exec()
