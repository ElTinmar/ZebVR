import sys
import math
import cv2
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QCheckBox, QLabel, QPushButton, QScrollArea, QSplitter, 
    QSlider, QComboBox, QSpinBox, QGroupBox
)
from PyQt6.QtGui import QPixmap, QColor, QPainter, QImage, QPolygonF, QPen
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal, QPointF

def np_to_qpixmap(arr):
    """Utility function to convert an HxWx3 uint8 NumPy array safely into a QPixmap."""
    h, w, c = arr.shape
    bytes_per_line = c * w
    qimg = QImage(arr.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
    return QPixmap.fromImage(qimg.copy())


class ComputeWorker(QThread):
    """Background worker thread dedicated solely to computing the statistical mode of NumPy arrays."""
    finished = pyqtSignal(np.ndarray)
    error = pyqtSignal(str)

    def __init__(self, arrays_list):
        super().__init__()
        self.arrays_list = arrays_list

    def run(self):
        try:
            if not self.arrays_list:
                return

            target_shape = self.arrays_list[0].shape
            for arr in self.arrays_list:
                if arr.shape != target_shape:
                    self.error.emit("Error: Selected images must have matching dimensions to compute mode.")
                    return

            stacked = np.stack(self.arrays_list, axis=0)
            sorted_stack = np.sort(stacked, axis=0)
            result_np = sorted_stack[sorted_stack.shape[0] // 2]
            
            self.finished.emit(result_np)

        except Exception as e:
            self.error.emit(f"Computation failed: {str(e)}")


class DrawPolyMask(QWidget):
    """Interactive canvas supporting live guide lines, vertex dragging, and canvas resets."""
    def __init__(self, fixed_size, parent=None):
        super().__init__(parent)
        self.fixed_size = fixed_size
        self.setFixedSize(self.fixed_size)
        
        self.base_np = None          
        self.inpainted_np = None     
        self.display_pixmap = None
        self.preview_mode = False    
        
        self.points = []             
        self.is_closed = False
        
        self.current_mouse_pos = None
        self.dragged_point_idx = None
        self.hovered_point_idx = None
        self.handle_radius = 6.0      
        
        self.setMouseTracking(True)
        
    def set_image(self, arr, clear_mask=True):
        self.base_np = arr.copy()
        raw_pixmap = np_to_qpixmap(self.base_np)
        self.display_pixmap = raw_pixmap.scaled(
            self.fixed_size, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        if clear_mask:
            self.clear_mask_data()
        self.update()

    def clear_mask_data(self):
        self.points = []
        self.is_closed = False
        self.inpainted_np = None
        self.preview_mode = False
        self.dragged_point_idx = None
        self.hovered_point_idx = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()

    def set_preview_mode(self, show_preview):
        if show_preview and self.inpainted_np is not None:
            self.preview_mode = True
            raw_pixmap = np_to_qpixmap(self.inpainted_np)
            self.display_pixmap = raw_pixmap.scaled(
                self.fixed_size, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
        else:
            self.preview_mode = False
            if self.base_np is not None:
                raw_pixmap = np_to_qpixmap(self.base_np)
                self.display_pixmap = raw_pixmap.scaled(
                    self.fixed_size, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
        self.update()

    def _find_hovered_vertex(self, pos):
        for idx, pt in enumerate(self.points):
            distance = math.hypot(pos.x() - pt.x(), pos.y() - pt.y())
            if distance <= self.handle_radius:
                return idx
        return None

    def mousePressEvent(self, event):
        if self.display_pixmap is None or self.preview_mode:
            return
        pos = event.position()
        if event.button() == Qt.MouseButton.LeftButton:
            hovered = self._find_hovered_vertex(pos)
            if hovered is not None:
                self.dragged_point_idx = hovered
                return
            if not self.is_closed:
                self.points.append(pos)
                self.inpainted_np = None
                self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            if len(self.points) >= 3 and not self.is_closed:
                self.is_closed = True
                self.update()

    def mouseMoveEvent(self, event):
        if self.display_pixmap is None or self.preview_mode:
            return
        pos = event.position()
        self.current_mouse_pos = pos
        if self.dragged_point_idx is not None:
            self.points[self.dragged_point_idx] = pos
            self.inpainted_np = None 
            self.update()
            return
        hovered = self._find_hovered_vertex(pos)
        if hovered != self.hovered_point_idx:
            self.hovered_point_idx = hovered
            if self.hovered_point_idx is not None:
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()
        if not self.is_closed and self.points:
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragged_point_idx = None

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.display_pixmap is None:
            painter.setPen(QPen(QColor("#bbb"), 2, Qt.PenStyle.DashLine))
            painter.setBrush(QColor("#fafafa"))
            painter.drawRect(self.rect())
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Workbench Area (Locked until Mode is Computed)")
            return
        dx = (self.width() - self.display_pixmap.width()) // 2
        dy = (self.height() - self.display_pixmap.height()) // 2
        painter.drawPixmap(dx, dy, self.display_pixmap)
        if not self.preview_mode and self.points:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            if self.is_closed:
                painter.setPen(QPen(QColor(255, 0, 0, 200), 2))
                painter.setBrush(QColor(255, 0, 0, 60))
                painter.drawPolygon(QPolygonF(self.points))
            else:
                painter.setPen(QPen(QColor(0, 120, 255), 2))
                for i in range(len(self.points) - 1):
                    painter.drawLine(self.points[i], self.points[i+1])
                if self.current_mouse_pos is not None:
                    painter.setPen(QPen(QColor(0, 120, 255, 140), 1, Qt.PenStyle.DashLine))
                    painter.drawLine(self.points[-1], self.current_mouse_pos)
            for idx, pt in enumerate(self.points):
                if idx == self.hovered_point_idx:
                    painter.setBrush(QColor(255, 69, 0)) 
                    r = self.handle_radius + 1
                else:
                    painter.setBrush(QColor(255, 215, 0)) 
                    r = self.handle_radius - 2
                painter.setPen(QPen(Qt.GlobalColor.black, 1))
                painter.drawEllipse(pt, r, r)

    def flatten_mask(self):
        if self.base_np is None or not self.is_closed or len(self.points) < 3:
            return None
        h, w, _ = self.base_np.shape
        dx = (self.width() - self.display_pixmap.width()) // 2
        dy = (self.height() - self.display_pixmap.height()) // 2
        scale_w = w / self.display_pixmap.width()
        scale_h = h / self.display_pixmap.height()
        mapped_points = []
        for pt in self.points:
            orig_x = (pt.x() - dx) * scale_w
            orig_y = (pt.y() - dy) * scale_h
            mapped_points.append([orig_x, orig_y])
        mask = np.zeros((h, w), dtype=np.uint8)
        pts_array = np.array(mapped_points, dtype=np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(mask, [pts_array], 255)
        return mask


class ImageItemWidget(QWidget):
    def __init__(self, np_array, index, thumb_size=240, parent=None):
        super().__init__(parent)
        self.index = index
        self.np_array = np_array
        self.base_pixmap = np_to_qpixmap(self.np_array)
        self.image_label = QLabel(self)
        self.image_label.setStyleSheet("border: 1px solid #ccc; background-color: #222;")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.checkbox = QCheckBox(self)
        self.update_thumbnail_size(thumb_size)

    def update_thumbnail_size(self, size):
        fixed_size = QSize(size, size)
        self.setFixedSize(fixed_size)
        self.image_label.setFixedSize(fixed_size)
        scaled_thumb = self.base_pixmap.scaled(fixed_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(scaled_thumb)
        cb_width = self.checkbox.sizeHint().width()
        self.checkbox.move(size - cb_width - 4, 4)

    def is_checked(self):
        return self.checkbox.isChecked()

    def set_checked(self, state):
        self.checkbox.setChecked(state)


class ImageGridModal(QDialog):
    def __init__(self, np_arrays, parent=None):
        super().__init__(parent)
        self.np_arrays = np_arrays  
        self.image_widgets = []
        self.processed_result_np = None  
        self.worker = None 
        self.current_thumb_size = 200 
        
        self.setWindowTitle("Background")
        self.resize(1250, 820)
        self.init_ui()
        self.update_workflow_state()
        
    def init_ui(self):
        window_layout = QVBoxLayout(self)
        
        # ACTIVE STATUS BANNER: Guides user through steps explicitly
        self.status_banner = QLabel(self)
        self.status_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_banner.setStyleSheet("font-size: 14px; font-weight: bold; padding: 2px; background-color: #eaeaea; border-radius: 4px; color: #333;")
        self.status_banner.setMaximumHeight(32)
        window_layout.addWidget(self.status_banner)
        
        main_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        
        # --- LEFT SIDE: Grid Selection ---
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        control_panel_layout = QHBoxLayout()
        self.master_checkbox = QCheckBox("Select All", self)
        self.master_checkbox.clicked.connect(self.toggle_select_all)
        control_panel_layout.addWidget(self.master_checkbox)
        
        control_panel_layout.addSpacing(15)
        control_panel_layout.addWidget(QLabel("Grid Size:", self))
        self.size_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.size_slider.setMinimum(120)
        self.size_slider.setMaximum(360)
        self.size_slider.setValue(self.current_thumb_size)
        self.size_slider.setFixedWidth(110)
        self.size_slider.valueChanged.connect(self.on_slider_size_changed)
        control_panel_layout.addWidget(self.size_slider)
        control_panel_layout.addStretch()
        
        self.btn_mode = QPushButton("Step 2: Compute Mode", self)
        self.btn_mode.setStyleSheet("font-weight: bold; padding: 6px 12px;")
        self.btn_mode.clicked.connect(self.compute_mode)
        control_panel_layout.addWidget(self.btn_mode)
        left_layout.addLayout(control_panel_layout)
        
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        grid_widget = QWidget()
        self.grid_layout = QGridLayout(grid_widget)
        self.grid_layout.setSpacing(6) 
        
        n = len(self.np_arrays)
        rows = math.ceil(math.sqrt(n)) if n > 0 else 1
        
        for i, arr in enumerate(self.np_arrays):
            row = i % rows
            col = i // rows
            img_widget = ImageItemWidget(arr, i, thumb_size=self.current_thumb_size, parent=self)
            self.grid_layout.addWidget(img_widget, row, col, Qt.AlignmentFlag.AlignCenter)
            self.image_widgets.append(img_widget)
            img_widget.checkbox.clicked.connect(self.update_master_checkbox_text)
            img_widget.checkbox.clicked.connect(self.update_workflow_state)
            
        scroll.setWidget(grid_widget)
        left_layout.addWidget(scroll)
        
        # --- RIGHT SIDE: Canvas, Options, Visualization toggles ---
        self.right_container = QWidget()
        right_layout = QVBoxLayout(self.right_container)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        self.preview_size = QSize(512, 512)
        self.canvas_widget = DrawPolyMask(self.preview_size, self)
        right_layout.addWidget(self.canvas_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.view_toggle_widget = QWidget()
        view_toggle_layout = QHBoxLayout(self.view_toggle_widget)
        view_toggle_layout.setContentsMargins(0, 0, 0, 0)
        self.btn_view_mask = QPushButton("Edit Mask (Before)", self)
        self.btn_view_result = QPushButton("View Inpaint (After)", self)
        self.btn_view_mask.setCheckable(True)
        self.btn_view_result.setCheckable(True)
        self.btn_view_mask.setChecked(True)
        self.btn_view_mask.clicked.connect(lambda: self.change_visualization_layer(False))
        self.btn_view_result.clicked.connect(lambda: self.change_visualization_layer(True))
        view_toggle_layout.addWidget(self.btn_view_mask)
        view_toggle_layout.addWidget(self.btn_view_result)
        right_layout.addWidget(self.view_toggle_widget)
        
        self.param_group = QGroupBox("Step 3: Optional Inpaint Parameters")
        param_layout = QGridLayout(self.param_group)
        
        param_layout.addWidget(QLabel("Algorithm:"), 0, 0)
        self.combo_algo = QComboBox(self)
        self.combo_algo.addItem("Navier-Stokes", cv2.INPAINT_NS)
        self.combo_algo.addItem("Telea", cv2.INPAINT_TELEA)
        param_layout.addWidget(self.combo_algo, 0, 1)
        
        param_layout.addWidget(QLabel("Radius (px):"), 1, 0)
        self.spin_radius = QSpinBox(self)
        self.spin_radius.setRange(1, 50)
        self.spin_radius.setValue(3)
        param_layout.addWidget(self.spin_radius, 1, 1)
        
        actions_sub_layout = QHBoxLayout()
        self.btn_clear_mask = QPushButton("Clear Mask", self)
        self.btn_clear_mask.clicked.connect(self.canvas_widget.clear_mask_data)
        
        self.btn_inpaint = QPushButton("Run Inpaint", self)
        self.btn_inpaint.setStyleSheet("background-color: #2da44e; color: white; font-weight: bold;")
        self.btn_inpaint.clicked.connect(self.inpaint_selected)
        
        actions_sub_layout.addWidget(self.btn_clear_mask, 1)
        actions_sub_layout.addWidget(self.btn_inpaint, 2)
        param_layout.addLayout(actions_sub_layout, 2, 0, 1, 2)
        right_layout.addWidget(self.param_group)
        
        main_splitter.addWidget(left_container)
        main_splitter.addWidget(self.right_container)
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 2)
        window_layout.addWidget(main_splitter)
        
        # --- BOTTOM ROW: Footer ---
        footer_layout = QHBoxLayout()
        footer_layout.addStretch() 
        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_apply = QPushButton("Step 4: Apply and Close", self)
        self.btn_apply.setStyleSheet("font-weight: bold; padding: 4px 15px;")
        self.btn_apply.setDefault(True) 
        
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_apply.clicked.connect(self.accept)
        
        footer_layout.addWidget(self.btn_cancel)
        footer_layout.addWidget(self.btn_apply)
        window_layout.addLayout(footer_layout)

    def update_workflow_state(self):
        """Active logic check block verifying UI accessibility states dynamically."""
        selected_count = len(self.get_selected_indices())
        
        # State A: No thumbnails selected
        if selected_count == 0:
            self.status_banner.setText("STEP 1: Please select one or more image thumbnails on the grid.")
            self.status_banner.setStyleSheet("font-size: 14px; font-weight: bold; padding: 2px; background-color: #fff3cd; border-radius: 4px; color: #856404;") # Warning Yellow
            self.btn_mode.setEnabled(False)
            self.right_container.setEnabled(False)
            self.btn_apply.setEnabled(False)
            return

        # State B: Thumbnails selected, but Mode hasn't run yet
        if self.processed_result_np is None:
            self.status_banner.setText("STEP 2: Click 'Compute Mode' to extract the background.")
            self.status_banner.setStyleSheet("font-size: 14px; font-weight: bold; padding: 2px; background-color: #cce5ff; border-radius: 4px; color: #004085;") # Action Blue
            self.btn_mode.setEnabled(True)
            self.btn_mode.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; padding: 6px 12px;")
            self.right_container.setEnabled(False)
            self.btn_apply.setEnabled(False)
            return

        # State C: Mode extraction calculation has succeeded
        self.btn_mode.setEnabled(True)
        self.btn_mode.setStyleSheet("font-weight: normal;")
        self.right_container.setEnabled(True)
        self.btn_apply.setEnabled(True) # Step 4 unlocked
        self.btn_apply.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 4px 15px;")
        
        if self.canvas_widget.inpainted_np is not None:
            self.status_banner.setText("STEP 4 COMPLETE: Inpaint generated. Press 'Apply and Close' to save.")
            self.status_banner.setStyleSheet("font-size: 14px; font-weight: bold; padding: 2px; background-color: #d4edda; border-radius: 4px; color: #155724;") # Green success
        else:
            self.status_banner.setText("STEP 3 (Optional): Draw on the canvas to mask blemishes and click 'Run Inpaint', or proceed straight to Step 4.")
            self.status_banner.setStyleSheet("font-size: 14px; font-weight: bold; padding: 2px; background-color: #e2e3e5; border-radius: 4px; color: #383d41;") # Neutral prompt

    def change_visualization_layer(self, show_preview_layer):
        self.btn_view_mask.setChecked(not show_preview_layer)
        self.btn_view_result.setChecked(show_preview_layer)
        self.canvas_widget.set_preview_mode(show_preview_layer)

    def on_slider_size_changed(self, value):
        self.current_thumb_size = value
        self.grid_layout.setEnabled(False)
        for widget in self.image_widgets:
            widget.update_thumbnail_size(value)
        self.grid_layout.setEnabled(True)

    def get_selected_indices(self):
        return [w.index for w in self.image_widgets if w.is_checked()]

    def get_result(self):
        return self.processed_result_np

    def toggle_select_all(self):
        intent_deselect = (self.master_checkbox.text() == "Deselect All")
        target_state = not intent_deselect
        for widget in self.image_widgets:
            widget.checkbox.blockSignals(True)
            widget.set_checked(target_state)
            widget.checkbox.blockSignals(False)
        self.master_checkbox.blockSignals(True)
        self.master_checkbox.setCheckState(Qt.CheckState.Checked if target_state else Qt.CheckState.Unchecked)
        self.master_checkbox.setText("Deselect All" if target_state else "Select All")
        self.master_checkbox.blockSignals(False)
        self.update_workflow_state()

    def update_master_checkbox_text(self):
        selected_count = len(self.get_selected_indices())
        total_count = len(self.image_widgets)
        self.master_checkbox.blockSignals(True)
        if selected_count == total_count:
            self.master_checkbox.setCheckState(Qt.CheckState.Checked)
            self.master_checkbox.setText("Deselect All")
        elif selected_count == 0:
            self.master_checkbox.setCheckState(Qt.CheckState.Unchecked)
            self.master_checkbox.setText("Select All")
        else:
            self.master_checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
            self.master_checkbox.setText("Deselect All")
        self.master_checkbox.blockSignals(False)

    def set_ui_enabled(self, enabled):
        self.btn_mode.setEnabled(enabled)
        self.master_checkbox.setEnabled(enabled)
        self.size_slider.setEnabled(enabled)
        for w in self.image_widgets:
            w.setEnabled(enabled)

    def compute_mode(self):
        selected_idx = self.get_selected_indices()
        if not selected_idx:
            return
        self.set_ui_enabled(False)
        selected_arrays = [self.np_arrays[idx] for idx in selected_idx]
        
        self.worker = ComputeWorker(selected_arrays)
        self.worker.finished.connect(self.on_compute_success)
        self.worker.error.connect(self.on_compute_failure)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)
        self.worker.start()

    def on_compute_success(self, result_np):
        self.set_ui_enabled(True)
        self.processed_result_np = result_np  
        self.canvas_widget.set_image(result_np, clear_mask=True)
        self.change_visualization_layer(False)
        self.update_workflow_state()

    def on_compute_failure(self, error_message):
        self.set_ui_enabled(True)
        self.processed_result_np = None
        self.update_workflow_state()

    def inpaint_selected(self):
        if self.canvas_widget.base_np is None:
            return
        src_image = self.canvas_widget.base_np.copy()
        mask = self.canvas_widget.flatten_mask()
        if mask is None or np.sum(mask) == 0:
            return 
            
        radius = self.spin_radius.value()
        algo = self.combo_algo.currentData()
        background = cv2.inpaint(src_image, mask, radius, algo)
        
        self.canvas_widget.inpainted_np = background
        self.processed_result_np = background
        
        self.change_visualization_layer(True)
        self.update_workflow_state()


# --- Dummy Execution Block ---
def create_dummy_np_array(width, height, rgb_color, pattern_offset=0):
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    arr[:, :, 0] = rgb_color[0]
    arr[:, :, 1] = rgb_color[1]
    arr[:, :, 2] = rgb_color[2]
    cv2.rectangle(arr, (width//3 + pattern_offset, height//3), (2*width//3 + pattern_offset, 2*height//3), (16, 16, 16), -1)
    return arr

if __name__ == "__main__":
    app = QApplication(sys.argv)
    colors = [
        (200, 50, 50),   (50, 200, 50),   (50, 50, 200),   (200, 200, 50),
        (50, 200, 200), (200, 50, 200), (200, 128, 50), (128, 128, 128),
        (220, 220, 220),(180, 180, 180),(50, 128, 128), (128, 128, 50)
    ]
    dummy_np_arrays = [create_dummy_np_array(800, 800, colors[i], pattern_offset=i*8) for i in range(12)]
    
    dialog = ImageGridModal(dummy_np_arrays)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Modal Closed: Result returned safely to processing pipeline.")