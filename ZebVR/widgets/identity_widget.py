from qtpy.QtWidgets import (
    QWidget, 
    QApplication,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem
)
from qtpy.QtCore import Signal, QPointF, QTimer, QSize
from qtpy.QtGui import QIcon, QPixmap, QImage
from typing import Dict, List
from numpy.typing import NDArray
import numpy as np
from pathlib import Path
from ZebVR.utils import FindCircularArenasDialog
from .background_modal import BackgroundModal
from .coordinate_system_widget import MultiCoordViewer

class IdentityWidget(QWidget):

    state_changed = Signal()
    DEFAULT_FILE: Path = Path('ZebVR/default/background.npy')
    REFRESH_RATE = 60
    
    def __init__(self, pix_per_mm: float = 30, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pix_per_mm = pix_per_mm
        self.axes_visible = True
        
        # Internal list keeping track of snapped NumPy images
        self.snapped_images: List[NDArray] = []
        
        self.viewer = MultiCoordViewer(self)
        self.viewer.state_changed.connect(self.state_changed)
        
        # Existing Control Buttons
        self.add_btn = QPushButton("Add ROI")
        self.add_btn.clicked.connect(lambda: self.viewer.add_coordinate_system(QPointF(150, 150)))
        
        self.clear_btn = QPushButton("Clear All")
        self.clear_btn.clicked.connect(self.reset)

        self.auto_btn = QPushButton("Auto find circular wells")
        self.auto_btn.clicked.connect(self.on_auto)

        # New Integration Buttons
        self.snap_btn = QPushButton("Snap Image")
        self.snap_btn.clicked.connect(self.snap_current_image)
        
        self.bg_modal_btn = QPushButton("Process Background")
        self.bg_modal_btn.clicked.connect(self.open_background_modal)
        self.bg_modal_btn.setEnabled(False)  # Disabled until we have at least 1 image

        # Horizontal Thumbnail List Widget
        self.thumb_strip = QListWidget()
        self.thumb_strip.setViewMode(QListWidget.ViewMode.IconMode)
        self.thumb_strip.setFlow(QListWidget.Flow.LeftToRight)  # Fixed: Flows horizontally correctly
        self.thumb_strip.setIconSize(QSize(80, 80))
        self.thumb_strip.setFixedHeight(100)
        self.thumb_strip.setMovement(QListWidget.Movement.Static)
        self.thumb_strip.setStyleSheet("background-color: #222; border: 1px solid #444;")

        # Assemble layouts
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.auto_btn)
        button_layout.addWidget(self.snap_btn)
        button_layout.addWidget(self.bg_modal_btn)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.thumb_strip)
        main_layout.addWidget(self.viewer)

        # Load standard canvas
        if self.DEFAULT_FILE.exists():
            self.image = np.load(self.DEFAULT_FILE)
        else:
            self.image = np.zeros((512, 512, 3), dtype=np.uint8)  # Defaulting to HxWx3 color array
        self.set_image(self.image)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_background_image)
        self.timer.start(1000 // self.REFRESH_RATE) 

    def snap_current_image(self):
        """Captures a snapshot copy of the current image, adds it to the storage pipeline, and draws a thumbnail."""
        if self.image is None:
            return
            
        img_copy = self.image.copy()
        self.snapped_images.append(img_copy)
        
        # Convert NumPy Array safely to QPixmap for previewing
        h, w = img_copy.shape[:2]
        c = img_copy.shape[2] if len(img_copy.shape) == 3 else 1
        bytes_per_line = c * w
        
        fmt = QImage.Format.Format_RGB888 if c == 3 else QImage.Format.Format_Grayscale8
        qimg = QImage(img_copy.data, w, h, bytes_per_line, fmt)
        pixmap = QPixmap.fromImage(qimg)
        
        # Append to UI Thumbnail Strip
        item = QListWidgetItem(QIcon(pixmap), f"Snap {len(self.snapped_images)}")
        self.thumb_strip.addItem(item)
        
        # Allow modal launcher processing
        self.bg_modal_btn.setEnabled(True)

    def open_background_modal(self):
        """Passes the snapped frames to BackgroundModal and overrides the canvas with computed results."""
        if not self.snapped_images:
            return
            
        modal = BackgroundModal(self.snapped_images, parent=self)
        if modal.exec_():
            result = modal.get_result()
            if result is not None:
                self.set_image(result)
                # Clear snap pool after an applied stack execution
                self.snapped_images.clear()
                self.thumb_strip.clear()
                self.bg_modal_btn.setEnabled(False)

    def update_background_image(self):
        self.viewer.set_background_image(self.image)

    def set_image(self, image: NDArray) -> None:
        self.image = image

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