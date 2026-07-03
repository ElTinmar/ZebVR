import sys
import math
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QCheckBox, QLabel, QPushButton, QScrollArea, QSplitter, QSlider
)
from PyQt6.QtGui import QPixmap, QColor, QPainter, QImage
from PyQt6.QtCore import Qt, QSize, QThread, pyqtSignal

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


class ImageItemWidget(QWidget):
    """A widget that converts a NumPy array to a dynamic display thumbnail and overlays a checkbox."""
    def __init__(self, np_array, index, thumb_size=240, parent=None):
        super().__init__(parent)
        self.index = index
        self.np_array = np_array
        
        # Keep a lazy evaluation cache of the full-res rendering pixmap to save conversion cycles
        self.base_pixmap = np_to_qpixmap(self.np_array)
        
        # Sub-component initializations
        self.image_label = QLabel(self)
        self.image_label.setStyleSheet("border: 1px solid #ccc; background-color: #222;")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.checkbox = QCheckBox(self)
        
        # Apply the initial size profile
        self.update_thumbnail_size(thumb_size)

    def update_thumbnail_size(self, size):
        """Updates internal frame geometries and downsamples pixel assets on the fly."""
        fixed_size = QSize(size, size)
        self.setFixedSize(fixed_size)
        self.image_label.setFixedSize(fixed_size)
        
        scaled_thumb = self.base_pixmap.scaled(
            fixed_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_thumb)
        
        # Recalculate checkbox corner layout footprint anchors
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
        self.current_thumb_size = 200 # App operational base size setting
        
        self.setWindowTitle("Scalable Image Grid Processor")
        self.resize(1100, 750)
        
        self.init_ui()
        
    def init_ui(self):
        window_layout = QVBoxLayout(self)
        main_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        
        # --- LEFT SIDE: Grid & Actions ---
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Top Interactive Control Action Panel Layout Line Container
        control_panel_layout = QHBoxLayout()
        
        self.master_checkbox = QCheckBox("Select All", self)
        self.master_checkbox.clicked.connect(self.toggle_select_all)
        control_panel_layout.addWidget(self.master_checkbox)
        
        # Slider implementation: Handles real-time adjustments
        control_panel_layout.addSpacing(20)
        control_panel_layout.addWidget(QLabel("Size:", self))
        self.size_slider = QSlider(Qt.Orientation.Horizontal, self)
        self.size_slider.setMinimum(120)
        self.size_slider.setMaximum(360)
        self.size_slider.setValue(self.current_thumb_size)
        self.size_slider.setFixedWidth(150)
        self.size_slider.valueChanged.connect(self.on_slider_size_changed)
        control_panel_layout.addWidget(self.size_slider)
        control_panel_layout.addStretch()
        
        self.btn_mode = QPushButton("Compute Mode", self)
        self.btn_inpaint = QPushButton("Inpaint Selected", self)
        self.btn_mode.clicked.connect(self.compute_mode)
        self.btn_inpaint.clicked.connect(self.inpaint_selected)
        
        control_panel_layout.addWidget(self.btn_mode)
        control_panel_layout.addWidget(self.btn_inpaint)
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
            
        scroll.setWidget(grid_widget)
        left_layout.addWidget(scroll)
        
        # --- RIGHT SIDE: Large Preview ---
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview_label = QLabel("No operation performed yet", self)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 2px dashed #aaa; background: #f5f5f5; padding: 10px;")
        
        self.preview_size = QSize(450, 450)
        self.preview_label.setFixedSize(self.preview_size)
        
        right_layout.addStretch()
        right_layout.addWidget(self.preview_label, alignment=Qt.AlignmentFlag.AlignCenter)
        right_layout.addStretch()
        
        main_splitter.addWidget(left_container)
        main_splitter.addWidget(right_container)
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 2)
        window_layout.addWidget(main_splitter)
        
        # --- BOTTOM ROW: Dialog Footer Actions ---
        footer_layout = QHBoxLayout()
        footer_layout.addStretch() 
        
        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_apply = QPushButton("Apply", self)
        self.btn_apply.setDefault(True) 
        
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_apply.clicked.connect(self.accept)
        
        footer_layout.addWidget(self.btn_cancel)
        footer_layout.addWidget(self.btn_apply)
        window_layout.addLayout(footer_layout)

    def on_slider_size_changed(self, value):
        """Loops through item handles to execute re-scale metrics across the active matrix."""
        self.current_thumb_size = value
        # Block layout execution loops temporarily during the mass updates to maintain performance
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

    def update_preview_from_numpy(self, arr):
        pixmap = np_to_qpixmap(arr)
        scaled_pixmap = pixmap.scaled(
            self.preview_size, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled_pixmap)

    def set_ui_enabled(self, enabled):
        self.btn_mode.setEnabled(enabled)
        self.btn_inpaint.setEnabled(enabled)
        self.btn_apply.setEnabled(enabled)
        self.master_checkbox.setEnabled(enabled)
        self.size_slider.setEnabled(enabled)
        for w in self.image_widgets:
            w.setEnabled(enabled)

    def compute_mode(self):
        selected_idx = self.get_selected_indices()
        if not selected_idx:
            self.preview_label.setPixmap(QPixmap()) 
            self.preview_label.setText("Please select images first.")
            self.processed_result_np = None
            return
            
        self.preview_label.setText("Calculating statistical pixel mode\non background thread...")
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
        self.update_preview_from_numpy(result_np)

    def on_compute_failure(self, error_message):
        self.set_ui_enabled(True)
        self.processed_result_np = None
        self.preview_label.setPixmap(QPixmap())
        self.preview_label.setText(error_message)

    def inpaint_selected(self):
        selected_idx = self.get_selected_indices()
        if not selected_idx:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("Please select images first.")
            self.processed_result_np = None
            return
            
        base_arr = self.np_arrays[selected_idx[0]].copy()
        h, w, _ = base_arr.shape
        base_arr[h//3:2*h//3, w//4:3*w//4, 0] = 255 
        base_arr[h//3:2*h//3, w//4:3*w//4, 1:] = 0  
        
        self.processed_result_np = base_arr
        self.update_preview_from_numpy(base_arr)


# --- Dummy Execution Block ---
def create_dummy_np_array(width, height, rgb_color):
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    arr[:, :, 0] = rgb_color[0]
    arr[:, :, 1] = rgb_color[1]
    arr[:, :, 2] = rgb_color[2]
    return arr

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    colors = [
        (255, 0, 0),   (0, 255, 0),   (0, 0, 255),   (255, 255, 0),
        (0, 255, 255), (255, 0, 255), (255, 128, 0), (128, 128, 128),
        (255, 255, 255),(200, 200, 200),(0, 128, 128), (128, 128, 0)
    ]
    
    dummy_np_arrays = [create_dummy_np_array(800, 800, colors[i]) for i in range(12)]
    dialog = ImageGridModal(dummy_np_arrays)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        output_array = dialog.get_result()
        print(f"Modal Accepted! Object type: {type(output_array)}")
    else:
        print("Modal Cancelled/Rejected.")