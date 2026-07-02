from qtpy.QtWidgets import (
    QWidget, 
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton
)
from qtpy.QtCore import Signal, QPointF
from typing import Dict
from numpy.typing import NDArray
import numpy as np
from pathlib import Path
from ZebVR.utils import FindCircularArenasDialog

from .coordinate_system_widget import MultiCoordViewer

class IdentityWidget(QWidget):

    # TODO merge this with background

    state_changed = Signal()
    DEFAULT_FILE: Path = Path('ZebVR/default/background.npy')

    def __init__(self, pix_per_mm: float = 30, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pix_per_mm = pix_per_mm
        self.axes_visible = True
        
        self.viewer = MultiCoordViewer(self)
        self.viewer.state_changed.connect(self.state_changed)
        
        self.add_btn = QPushButton("Add ROI")
        self.add_btn.clicked.connect(lambda: self.viewer.add_coordinate_system(QPointF(150, 150)))
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.reset)

        self.auto_btn = QPushButton("Auto find circular wells")
        self.auto_btn.clicked.connect(self.on_auto)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.auto_btn)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.viewer)

        # Load standard canvas
        if self.DEFAULT_FILE.exists():
            self.image = np.load(self.DEFAULT_FILE)
        else:
            self.image = np.zeros((512, 512), dtype=np.uint8)
        self.set_image(self.image)

    def set_image(self, image: NDArray) -> None:
        self.image = image
        self.viewer.set_background_image(self.image)
        self.state_changed.emit()

    def reset(self) -> None:
        self.viewer.clear_coordinate_systems()
        self.state_changed.emit()

    def set_axes_visible(self, visible: bool) -> None:
        self.axes_visible = visible
        self.viewer.set_axes_visible(visible)
        self.state_changed.emit()

    def set_pix_per_mm(self, pix_per_mm: float) -> None:
        self.pix_per_mm = pix_per_mm

    def get_state(self) -> Dict:
        return self.viewer.get_state()
    
    def set_state(self, state: Dict) -> None:
        self.viewer.set_state(state)
        
    def on_auto(self):
        modal = FindCircularArenasDialog(
            image = self.image,
            pix_per_mm = self.pix_per_mm
        )
        modal.data.connect(self.handle_auto)
        modal.exec_()

    def handle_auto(self, circles, rois, annotated_image):
        state = {}
        state['identities'] = {}
        for idx, (circle, bbox) in enumerate(zip(circles, rois)):
            state['identities'][idx] = {}
            state['identities'][idx]['bbox_rect'] = bbox
            state['identities'][idx]['centroid'] = circle[:2] - bbox[:2]
            state['identities'][idx]['axes'] = [[1,0],[0,1]]
            state['identities'][idx]['axes_visible'] = False

        self.set_state(state)
        self.state_changed.emit()

if __name__ == "__main__":
    
    app = QApplication([])
    window = IdentityWidget()
    window.show()
    app.exec()
