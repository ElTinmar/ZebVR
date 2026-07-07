import numpy as np
from typing import Dict, List
from numpy.typing import NDArray

from qtpy.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QScrollArea, QLabel, QProgressBar
)
from qtpy.QtCore import Signal, QPointF, QTimer, Qt
from qtpy.QtGui import QImage, QPixmap

from .coordinate_system_widget import MultiCoordViewer
from .background_modal import BackgroundModal
from ZebVR.utils import FindCircularArenasDialog
from qt_widgets import LabeledSpinBox, LabeledDoubleSpinBox

class IdentityWidget(QWidget):
    state_changed = Signal()
    REFRESH_RATE = 60
    
    def __init__(self, pix_per_mm: float = 30, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pix_per_mm = pix_per_mm
        self.showing_background = False
        
        self.snapped_images: List[NDArray] = []
        self.image = np.zeros((512, 512, 3), dtype=np.uint8)
        self.background_image = np.zeros((512, 512, 3), dtype=np.uint8)        
        
        # Initialize Viewer
        self.viewer = MultiCoordViewer(self)
        self.viewer.state_changed.connect(self.state_changed)

        # UI Elements
        self.layer_btn = QPushButton("BG", self.viewer)
        self.layer_btn.setCheckable(True)
        self.layer_btn.setFixedSize(32, 24)  
        self.layer_btn.move(8, 8)
        self.layer_btn.clicked.connect(self.toggle_layer)
        self.layer_btn.setStyleSheet("""
            QPushButton { background-color: rgba(0, 0, 0, 80); color: rgba(255, 255, 255, 140); border: 1px solid rgba(255, 255, 255, 40); border-radius: 3px; font-size: 10px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(0, 0, 0, 160); color: #fff; }
            QPushButton:checked { background-color: rgba(40, 167, 69, 120); }
        """)
        
        # Action Buttons
        self.add_btn = QPushButton("Add ROI")
        self.add_btn.clicked.connect(lambda: self.viewer.add_coordinate_system(QPointF(150, 150)))
        
        self.clear_btn = QPushButton("Clear ROI")
        self.clear_btn.clicked.connect(self.clear_roi)
        
        self.auto_btn = QPushButton("Auto find circular wells")
        self.auto_btn.clicked.connect(self.on_auto)
        
        self.snap_btn = QPushButton("Snap Image")
        self.snap_btn.clicked.connect(self.snap_current_image)

        self.clear_snap_btn = QPushButton("Clear Snapshots")
        self.clear_snap_btn.clicked.connect(self.clear_snaps)
        
        self.bg_modal_btn = QPushButton("Process Background")
        self.bg_modal_btn.clicked.connect(self.open_background_modal)
        self.bg_modal_btn.setEnabled(False)  

        self.count_input = LabeledSpinBox()
        self.count_input.setText("Count:")
        self.count_input.setValue(10)
        self.count_input.setMinimum(1)
        self.count_input.setMaximum(1000)

        self.interval_input = LabeledDoubleSpinBox()
        self.interval_input.setText("Interval (s):")
        self.interval_input.setValue(1.0)
        self.interval_input.setMinimum(0.01)
        self.interval_input.setMaximum(60.0)

        self.start_auto_btn = QPushButton("Start Auto Capture")
        self.start_auto_btn.setCheckable(True)
        self.start_auto_btn.clicked.connect(self.toggle_auto_capture)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()

        # Capture Timer
        self.capture_timer = QTimer(self)
        self.capture_timer.timeout.connect(self._process_auto_capture)
        self.snaps_remaining = 0

        # Thumbnail Area
        self.thumb_scroll = QScrollArea()
        self.thumb_scroll.setFixedHeight(120)
        self.thumb_scroll.setWidgetResizable(True)
        self.thumb_container = QWidget()
        self.thumb_layout = QHBoxLayout(self.thumb_container)
        self.thumb_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.thumb_scroll.setWidget(self.thumb_container)

        # Layout Assembly
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(self._create_hlayout([self.add_btn, self.clear_btn, self.auto_btn]))
        main_layout.addWidget(self.viewer, 1)
        main_layout.addLayout(self._create_hlayout([self.snap_btn, self.clear_snap_btn, self.bg_modal_btn]))
        main_layout.addLayout(self._create_hlayout([self.count_input, self.interval_input, self.start_auto_btn]))
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.thumb_scroll)
            
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_viewer_image)
        self.timer.start(1000 // self.REFRESH_RATE) 

    def _create_hlayout(self, widgets):
        l = QHBoxLayout()
        for w in widgets: l.addWidget(w)
        return l

    def toggle_auto_capture(self, checked: bool):
        if checked:
            self.snaps_remaining = self.count_input.value()
            interval_ms = int(self.interval_input.value() * 1000)
            self.progress_bar.setRange(0, self.snaps_remaining)
            self.progress_bar.setValue(0)
            self.progress_bar.show()
            self.start_auto_btn.setText("Stop Capture")
            self.capture_timer.start(interval_ms)
            self._process_auto_capture()
        else:
            self.stop_auto_capture()

    def stop_auto_capture(self):
        self.capture_timer.stop()
        self.progress_bar.hide()
        self.start_auto_btn.setChecked(False)
        self.start_auto_btn.setText("Start Auto Capture")

    def _process_auto_capture(self):
        if self.snaps_remaining <= 0:
            self.stop_auto_capture()
            return
        
        self.snap_current_image()
        self.snaps_remaining -= 1
        self.progress_bar.setValue(self.progress_bar.maximum() - self.snaps_remaining)

    def toggle_layer(self, checked: bool):
        self.showing_background = checked
        if self.showing_background:
            self.timer.stop()
            self.viewer.set_image(self.background_image)
        else:
            self.timer.start(1000 // self.REFRESH_RATE)

    def snap_current_image(self):
        if self.image is None: return
        img_copy = self.image.copy()
        self.snapped_images.append(img_copy)
        
        h, w = img_copy.shape[:2]
        fmt = QImage.Format.Format_RGB888 if len(img_copy.shape) == 3 else QImage.Format.Format_Grayscale8
        qimg = QImage(img_copy.data, w, h, img_copy.strides[0], fmt)
        pixmap = QPixmap.fromImage(qimg).scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        lbl = QLabel()
        lbl.setPixmap(pixmap)
        lbl.setFixedSize(80, 80)
        self.thumb_layout.addWidget(lbl)
        self.bg_modal_btn.setEnabled(True)

    def open_background_modal(self):
        modal = BackgroundModal(self.snapped_images, parent=self)
        if modal.exec_():
            background_image = modal.get_result()
            if background_image is None:
                return 
            
            img_h, img_w = background_image.shape[:2]
            
            if self.background_image.shape[:2] != (img_h, img_w):
                self.background_image = np.zeros_like(background_image)

            for sys_item in self.viewer.coordinate_systems:
                if sys_item.is_locked:
                    continue
                    
                item_state = sys_item.get_state()
                x, y, w, h = item_state["bbox_rect"]
                
                x1 = max(0, min(x, img_w))
                y1 = max(0, min(y, img_h))
                x2 = max(0, min(x + w, img_w))
                y2 = max(0, min(y + h, img_h))
                
                if (x2 > x1) and (y2 > y1):
                    self.background_image[y1:y2, x1:x2] = background_image[y1:y2, x1:x2].copy() 
            
            self.clear_thumbnails()
            self.layer_btn.setChecked(True)
            self.toggle_layer(True)
            self.state_changed.emit()

    def clear_thumbnails(self):
        self.snapped_images.clear()
        while self.thumb_layout.count():
            item = self.thumb_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.bg_modal_btn.setEnabled(False)

    def update_viewer_image(self):
        if not self.showing_background:
            self.viewer.set_image(self.image)

    def set_image(self, image: NDArray) -> None:
        self.image = image

    def clear_roi(self):
        self.viewer.clear_coordinate_systems()
        self.state_changed.emit()

    def clear_snaps(self):
        self.clear_thumbnails()
        self.state_changed.emit()

    def set_pix_per_mm(self, pix_per_mm: float) -> None:
        self.pix_per_mm = pix_per_mm

    def get_state(self) -> Dict:
        state = self.viewer.get_state()
        state['background'] = self.background_image
        return state
    
    def set_state(self, state: Dict) -> None:
        self.viewer.set_state(state)
        #self.background_image = state['background']
        
    def on_auto(self):
        modal = FindCircularArenasDialog(image=self.image, pix_per_mm=self.pix_per_mm)
        modal.data.connect(self.handle_auto)
        modal.exec_()

    def handle_auto(self, circles, rois, annotated_image):
        state = {'identities': {}}
        for idx, (circle, bbox) in enumerate(zip(circles, rois)):
            state['identities'][idx] = {
                'bbox_rect': bbox,
                'centroid': circle[:2] - bbox[:2],
                'axes': [[0,1],[-1,0]],
            }
        self.set_state(state)
        self.state_changed.emit()
