import numpy as np
import cv2
from typing import Tuple, Optional
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (
    QApplication, 
    QDialog, 
    QVBoxLayout, 
    QHBoxLayout, 
    QFormLayout,
    QPushButton, 
    QGraphicsScene, 
    QMessageBox, 
    QDialogButtonBox, 
    QDoubleSpinBox
)
from qt_widgets import ZoomableGraphicsView

def find_circular_arenas(        
        image: np.ndarray, 
        pix_per_mm: float,
        detection_tolerance_mm: float,
        well_radius_mm: float,
        distance_between_well_centers_mm: float,
        gradient_threshold_high: float = 50,
        circle_detection_threshold: float = 30,
        bounding_box_tolerance_mm: float = 1
    ) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """
    Detect circular arenas (e.g. wells) and compute bounding boxes around them.

    Args:
        image: Grayscale or BGR input image.
        pix_per_mm: Conversion factor from millimeters to pixels.
        detection_tolerance_mm: Allowed tolerance for radius and spacing.
        well_radius_mm: Expected radius of the wells in mm.
        distance_between_well_centers_mm: Expected distance between adjacent well centers in mm.
        gradient_threshold_high: First parameter to Canny edge detector (HoughCircles param1).
        circle_detection_threshold: Accumulator threshold for circle centers (HoughCircles param2).
        bounding_box_tolerance_mm: Additional padding for bounding boxes in mm.

    Returns:
        circles_px: np.ndarray of shape (N, 3) with (x, y, radius) in pixels.
        ROIs_px: np.ndarray of shape (N, 4) with (x_min, y_min, x_max, y_max) in pixels.
        detected_wells: BGR image with circles and bounding boxes drawn.
        Returns None if no circles were detected.
    """

    detection_tolerance_px = int(detection_tolerance_mm * pix_per_mm) 
    bounding_box_tolerance_px = int(bounding_box_tolerance_mm * pix_per_mm) 
    circle_radius_px = int(pix_per_mm * well_radius_mm)
    well_distance_px = int(pix_per_mm * distance_between_well_centers_mm)

    min_radius_px = circle_radius_px - detection_tolerance_px
    max_radius_px = circle_radius_px + detection_tolerance_px
    min_distance_px = well_distance_px - detection_tolerance_px

    circles_px = cv2.HoughCircles(
        image,
        cv2.HOUGH_GRADIENT,
        dp = 1,
        minDist = min_distance_px,
        param1 = gradient_threshold_high,
        param2 = circle_detection_threshold,
        minRadius = min_radius_px,
        maxRadius = max_radius_px
    )

    if circles_px is None:
        return None

    circles_px = np.around(circles_px[0]).astype(np.uint16)

    # overlay detected circles and bounding boxes
    if len(image.shape) == 2:  # grayscale
        detected_wells = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        detected_wells = image.copy()

    
    bounding_boxes = []
    h, w = detected_wells.shape[:2]

    for x, y, r in circles_px:
        center = (x, y)
        cv2.circle(detected_wells, center, r, (0, 255, 0), 2)
        cv2.circle(detected_wells, center, 2, (0, 0, 255), 3)

        x_min = max(0, x - (r + bounding_box_tolerance_px))
        y_min = max(0, y - (r + bounding_box_tolerance_px))
        x_max = min(w - 1, x + (r + bounding_box_tolerance_px))
        y_max = min(h - 1, y + (r + bounding_box_tolerance_px))

        cv2.rectangle(detected_wells, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)
        bounding_boxes.append((x_min, y_min, x_max-x_min, y_max-y_min))

    ROIs = np.array(bounding_boxes, dtype=np.uint16)

    # Sort circles for consistent ordering (top-to-bottom, then left-to-right)
    sort_idx = np.lexsort((circles_px[:, 0], circles_px[:, 1]))
    circles = circles_px[sort_idx]
    ROIs = ROIs[sort_idx]

    return circles, ROIs, detected_wells

class FindCircularArenasDialog(QDialog):
    parametersAccepted = pyqtSignal(dict)
    resultsReady = pyqtSignal(np.ndarray, np.ndarray, np.ndarray)

    def __init__(self, image: np.ndarray, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Find Circular Arenas")
        self.setModal(True)

        self.image = image
        self.detected_image = image.copy()
        self.results = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Graphics view
        self.scene = QGraphicsScene()
        self.view = ZoomableGraphicsView()
        self.view.setScene(self.scene)
        layout.addWidget(self.view)

        # Parameter form
        form = QFormLayout()

        self.pix_per_mm = QDoubleSpinBox(); self.pix_per_mm.setValue(10); self.pix_per_mm.setDecimals(2)
        self.detection_tolerance_mm = QDoubleSpinBox(); self.detection_tolerance_mm.setValue(0.5)
        self.radius_mm = QDoubleSpinBox(); self.radius_mm.setValue(5.0)
        self.distance_mm = QDoubleSpinBox(); self.distance_mm.setValue(12.0)
        self.gradient_thresh = QDoubleSpinBox(); self.gradient_thresh.setValue(50)
        self.circle_thresh = QDoubleSpinBox(); self.circle_thresh.setValue(30)
        self.box_tolerance_mm = QDoubleSpinBox(); self.box_tolerance_mm.setValue(1.0)

        form.addRow("Pixels per mm:", self.pix_per_mm)
        form.addRow("Detection tolerance (mm):", self.detection_tolerance_mm)
        form.addRow("Well radius (mm):", self.radius_mm)
        form.addRow("Distance between centers (mm):", self.distance_mm)
        form.addRow("Gradient threshold:", self.gradient_thresh)
        form.addRow("Circle detection threshold:", self.circle_thresh)
        form.addRow("Bounding box tolerance (mm):", self.box_tolerance_mm)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        self.detect_btn = QPushButton("Detect Circles")
        self.detect_btn.clicked.connect(self.on_detect)
        btn_layout.addWidget(self.detect_btn)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.on_accept)
        button_box.rejected.connect(self.reject)
        btn_layout.addWidget(button_box)

        layout.addLayout(btn_layout)

        self._update_display(self.image)

    def _update_display(self, image):
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        qimage = QImage(rgb.data, rgb.shape[1], rgb.shape[0], rgb.strides[0], QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)
        self.scene.clear()
        self.scene.addPixmap(pixmap)
        self.scene.setSceneRect(pixmap.rect())

    def on_detect(self):
        params = dict(
            pix_per_mm=self.pix_per_mm.value(),
            detection_tolerance_mm=self.detection_tolerance_mm.value(),
            well_radius_mm=self.radius_mm.value(),
            distance_between_well_centers_mm=self.distance_mm.value(),
            gradient_threshold_high=self.gradient_thresh.value(),
            circle_detection_threshold=self.circle_thresh.value(),
            bounding_box_tolerance_mm=self.box_tolerance_mm.value()
        )

        gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        result = find_circular_arenas(gray, **params)

        if result is None:
            QMessageBox.warning(self, "No Circles", "No circles were detected.")
            return

        circles, rois, annotated = result
        self.results = (circles, rois, annotated)
        self.detected_image = annotated
        self._update_display(annotated)

    def on_accept(self):
        if self.results:
            circles, rois, annotated = self.results
            self.resultsReady.emit(circles, rois, annotated)

        params = dict(
            pix_per_mm=self.pix_per_mm.value(),
            detection_tolerance_mm=self.detection_tolerance_mm.value(),
            well_radius_mm=self.radius_mm.value(),
            distance_between_well_centers_mm=self.distance_mm.value(),
            gradient_threshold_high=self.gradient_thresh.value(),
            circle_detection_threshold=self.circle_thresh.value(),
            bounding_box_tolerance_mm=self.box_tolerance_mm.value()
        )
        self.parametersAccepted.emit(params)
        self.accept()


if __name__ == "__main__":
    app = QApplication([])

    image = cv2.imread("test_image.jpg")
    if image is None:
        raise FileNotFoundError("Please place a 'test_image.jpg' in the working directory.")

    dlg = FindCircularArenasDialog(image)
    dlg.resultsReady.connect(lambda c, r, a: print(f"Detected {len(c)} circles"))
    if dlg.exec_() == QDialog.Accepted:
        print("Parameters accepted!")

    app.exec_()
