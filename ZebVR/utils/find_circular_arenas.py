import numpy as np
import cv2
from typing import Tuple, Optional
from qtpy.QtCore import  Signal
from qtpy.QtWidgets import (
    QApplication, 
    QDialog, 
    QVBoxLayout, 
    QHBoxLayout, 
    QFormLayout,
    QPushButton, 
    QGraphicsScene, 
    QMessageBox, 
    QDialogButtonBox, 
    QDoubleSpinBox,
    QGraphicsPixmapItem
)
from image_tools import im2gray
from qt_widgets import (
    ZoomableGraphicsView, 
    NDarray_to_QPixmap,
    WorkerThread,
    BusyOverlay
)

def find_circular_arenas(        
        image: np.ndarray, 
        pix_per_mm: float,
        detection_tolerance_mm: float,
        well_radius_mm: float,
        distance_between_well_centers_mm: float,
        gradient_threshold_high: float = 50,
        circle_detection_threshold: float = 30,
        bounding_box_tolerance_mm: float = 1,
        blur_kernel_large_mm: float = 2.5,
        blur_kernel_small_mm: float = 0.3,
    ) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]:
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
        blurred: processed image used for hough transform.
        detected_wells: BGR image with circles and bounding boxes drawn.
        Returns None if no circles were detected.
    """

    detection_tolerance_px = int(detection_tolerance_mm * pix_per_mm) 
    bounding_box_tolerance_px = int(bounding_box_tolerance_mm * pix_per_mm) 
    circle_radius_px = int(pix_per_mm * well_radius_mm)
    well_distance_px = int(pix_per_mm * distance_between_well_centers_mm)
    blur_kernel_large_px = int(pix_per_mm * blur_kernel_large_mm) | 1
    blur_kernel_small_px =  int(pix_per_mm * blur_kernel_small_mm) | 1

    min_radius_px = circle_radius_px - detection_tolerance_px
    max_radius_px = circle_radius_px + detection_tolerance_px
    min_distance_px = well_distance_px - detection_tolerance_px

    gray = im2gray(image)
    background = cv2.GaussianBlur(gray, (blur_kernel_large_px, blur_kernel_large_px), 0)
    flat = cv2.divide(gray, background, scale=255)
    blurred = cv2.GaussianBlur(flat, (blur_kernel_small_px, blur_kernel_small_px), 0)

    circles_px = cv2.HoughCircles(
        blurred,
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

        # numpy uint16 can overflow, convert to regular int
        x = int(x)
        y = int(y)
        r = int(r)
        
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

    return circles, ROIs, blurred, detected_wells

class FindCircularArenasDialog(QDialog):

    data =  Signal(np.ndarray, np.ndarray, np.ndarray)
    RESIZED_HEIGHT = 512

    def __init__(
            self, 
            image: np.ndarray, 
            pix_per_mm: float,
            detection_tolerance_mm: float = 2.0,
            radius_mm: float = 9.75,
            distance_mm: float = 22.0,
            gradient_thresh: float = 50,
            circle_thresh: float = 30,
            box_tolerance_mm: float = 1.0,
            blur_kernel_large_mm: float = 2.5,
            blur_kernel_small_mm: float = 0.3,
            parent=None
        ):
        super().__init__(parent)

        self.pix_per_mm = pix_per_mm
        self.detection_tolerance_mm = detection_tolerance_mm
        self.radius_mm = radius_mm
        self.distance_mm = distance_mm
        self.gradient_thresh = gradient_thresh
        self.circle_thresh = circle_thresh
        self.box_tolerance_mm = box_tolerance_mm
        self.blur_kernel_large_mm = blur_kernel_large_mm
        self.blur_kernel_small_mm = blur_kernel_small_mm
        self.setWindowTitle("Find Circular Arenas")
        self.setModal(True)

        self.image = image
        self.detected_image = image.copy()
        self.results = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        image_layout = QHBoxLayout()

        # Graphics view
        self.scene = QGraphicsScene()
        self.annotated_image = QGraphicsPixmapItem()
        self.scene.addItem(self.annotated_image)
        self.view = ZoomableGraphicsView()
        self.view.setScene(self.scene)

        self.scene_processed = QGraphicsScene()
        self.processed_image = QGraphicsPixmapItem()
        self.scene_processed.addItem(self.processed_image)
        self.view_processed = ZoomableGraphicsView()
        self.view_processed.setScene(self.scene_processed)

        image_layout.addWidget(self.view)
        image_layout.addWidget(self.view_processed)
        layout.addLayout(image_layout)

        self.busy = BusyOverlay(self)

        # Parameter form
        form = QFormLayout()

        self.sb_pix_per_mm = QDoubleSpinBox(); self.sb_pix_per_mm.setValue(self.pix_per_mm); self.sb_pix_per_mm.setDecimals(2)
        self.sb_detection_tolerance_mm = QDoubleSpinBox(); self.sb_detection_tolerance_mm.setValue(self.detection_tolerance_mm)
        self.sb_radius_mm = QDoubleSpinBox(); self.sb_radius_mm.setValue(self.radius_mm)
        self.sb_distance_mm = QDoubleSpinBox(); self.sb_distance_mm.setValue(self.distance_mm)
        self.sb_gradient_thresh = QDoubleSpinBox(); self.sb_gradient_thresh.setValue(self.gradient_thresh)
        self.sb_circle_thresh = QDoubleSpinBox(); self.sb_circle_thresh.setValue(self.circle_thresh)
        self.sb_box_tolerance_mm = QDoubleSpinBox(); self.sb_box_tolerance_mm.setValue(self.box_tolerance_mm)
        self.sb_blur_kernel_large_mm = QDoubleSpinBox(); self.sb_blur_kernel_large_mm.setValue(self.blur_kernel_large_mm)
        self.sb_blur_kernel_small_mm = QDoubleSpinBox(); self.sb_blur_kernel_small_mm.setValue(self.blur_kernel_small_mm)

        form.addRow("Pixels per mm:", self.sb_pix_per_mm)
        form.addRow("Detection tolerance (mm):", self.sb_detection_tolerance_mm)
        form.addRow("Well radius (mm):", self.sb_radius_mm)
        form.addRow("Distance between centers (mm):", self.sb_distance_mm)
        form.addRow("Gradient threshold:", self.sb_gradient_thresh)
        form.addRow("Circle detection threshold:", self.sb_circle_thresh)
        form.addRow("Bounding box tolerance (mm):", self.sb_box_tolerance_mm)
        form.addRow("Blur kernel large (mm):", self.sb_blur_kernel_large_mm)
        form.addRow("Blur kernel small (mm):", self.sb_blur_kernel_small_mm)

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

        self._update_display(self.image, self.image)

    def _update_display(self, processed, annotated):

        h, w = annotated.shape[:2]
        resized_width = int(self.RESIZED_HEIGHT * w/h)
        image_resized = cv2.resize(annotated,(resized_width,self.RESIZED_HEIGHT))
        self.annotated_image.setPixmap(NDarray_to_QPixmap(image_resized))

        h, w = processed.shape[:2]
        resized_width = int(self.RESIZED_HEIGHT * w/h)
        image_resized = cv2.resize(processed,(resized_width,self.RESIZED_HEIGHT))
        self.processed_image.setPixmap(NDarray_to_QPixmap(image_resized))

    def on_detect(self):
        params = dict(
            pix_per_mm=self.sb_pix_per_mm.value(),
            detection_tolerance_mm=self.sb_detection_tolerance_mm.value(),
            well_radius_mm=self.sb_radius_mm.value(),
            distance_between_well_centers_mm=self.sb_distance_mm.value(),
            gradient_threshold_high=self.sb_gradient_thresh.value(),
            circle_detection_threshold=self.sb_circle_thresh.value(),
            bounding_box_tolerance_mm=self.sb_box_tolerance_mm.value(),
            blur_kernel_large_mm=self.sb_blur_kernel_large_mm.value(),
            blur_kernel_small_mm=self.sb_blur_kernel_small_mm.value()
        )

        self.busy.show_overlay()
        self.thread = WorkerThread(find_circular_arenas, self.image, **params)
        self.thread.result.connect(self.handle_results)
        self.thread.exception.connect(self.handle_exception)
        self.thread.start()

    def handle_results(self, detection: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]]):
        
        self.busy.hide_overlay()

        if detection is None:
            QMessageBox.warning(self, "No Circles", "No circles were detected.")
            return
        
        circles, rois, processed, annotated = detection
        self.results = (circles, rois, processed, annotated)
        self.detected_image = annotated
        self._update_display(processed, annotated)

    def handle_exception(self, exception: Exception):
        print(exception)

    def on_accept(self):
        if self.results:
            circles, rois, _, annotated = self.results
            self.data.emit(circles, rois, annotated)

        self.accept()

    def closeEvent(self, event):
        if hasattr(self, "thread") and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()

        super().closeEvent(event)

if __name__ == "__main__":

    app = QApplication([])

    image = cv2.imread("ZebVR/resources/background_example.png")
    if image is None:
        raise FileNotFoundError("Please place a 'test_image.jpg' in the working directory.")

    dlg = FindCircularArenasDialog(image, pix_per_mm=35)
    dlg.data.connect(lambda c, r, a: print(f"Detected {len(c)} circles"))
    if dlg.exec_() == QDialog.Accepted:
        print("Parameters accepted!")

