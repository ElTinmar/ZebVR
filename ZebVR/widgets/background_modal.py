import sys
import math
from PyQt6.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QCheckBox, QLabel, QPushButton, QScrollArea, QSplitter
)
from PyQt6.QtGui import QPixmap, QColor, QPainter
from PyQt6.QtCore import Qt, QSize

class ImageItemWidget(QWidget):
    """A widget that scales any input image to a fixed thumbnail size and overlays a checkbox."""
    def __init__(self, pixmap, index, thumb_size=240, parent=None):
        super().__init__(parent)
        self.index = index
        self.pixmap = pixmap
        
        # Enforce a strict uniform footprint for the thumbnail widget box
        self.fixed_size = QSize(thumb_size, thumb_size)
        self.setFixedSize(self.fixed_size)
        
        # Image display label (fills the widget exactly)
        self.image_label = QLabel(self)
        self.image_label.setFixedSize(self.fixed_size)
        self.image_label.setStyleSheet("border: 1px solid #ccc; background-color: #222;")
        
        # Scale the arbitrary input pixmap to smoothly fit our standardized thumbnail size
        scaled_thumb = pixmap.scaled(
            self.fixed_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled_thumb)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Checkbox overlay
        self.checkbox = QCheckBox(self)
        
        # Position the checkbox dynamically in the top-right corner of the fixed box
        cb_width = self.checkbox.sizeHint().width()
        self.checkbox.move(thumb_size - cb_width - 4, 4)

    def is_checked(self):
        return self.checkbox.isChecked()

    def set_checked(self, state):
        self.checkbox.setChecked(state)


class ImageGridModal(QDialog):
    def __init__(self, pixmaps, parent=None):
        super().__init__(parent)
        self.pixmaps = pixmaps
        self.image_widgets = []
        
        self.setWindowTitle("Image Grid Processor")
        self.resize(1000, 700)
        
        self.init_ui()
        
    def init_ui(self):
        # Master Window Layout
        window_layout = QVBoxLayout(self)
        
        # Main layout splitter to separate Grid (left) and Preview (right)
        main_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        
        # --- LEFT SIDE: Grid & Actions ---
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Action Panel (Master Checkbox + Buttons)
        btn_layout = QHBoxLayout()
        
        # Master select/deselect checkbox
        self.master_checkbox = QCheckBox("Select All", self)
        self.master_checkbox.clicked.connect(self.toggle_select_all) # Switched to .clicked for user intent
        btn_layout.addWidget(self.master_checkbox)
        
        self.btn_mode = QPushButton("Compute Mode", self)
        self.btn_inpaint = QPushButton("Inpaint Selected", self)
        
        self.btn_mode.clicked.connect(self.compute_mode)
        self.btn_inpaint.clicked.connect(self.inpaint_selected)
        
        btn_layout.addWidget(self.btn_mode)
        btn_layout.addWidget(self.btn_inpaint)
        left_layout.addLayout(btn_layout)
        
        # Scroll area for the grid
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(4) 
        
        # Calculate dynamic rows: ceil(sqrt(n))
        n = len(self.pixmaps)
        rows = math.ceil(math.sqrt(n)) if n > 0 else 1
        
        # Populate the grid using rows as the primary constraint
        for i, pixmap in enumerate(self.pixmaps):
            row = i % rows
            col = i // rows
            
            img_widget = ImageItemWidget(pixmap, i, thumb_size=240, parent=self)
            grid_layout.addWidget(img_widget, row, col, Qt.AlignmentFlag.AlignCenter)
            self.image_widgets.append(img_widget)
            
            # Link manual checks to track and update master checkbox natively
            img_widget.checkbox.clicked.connect(self.update_master_checkbox_text)
            
        scroll.setWidget(grid_widget)
        left_layout.addWidget(scroll)
        
        # --- RIGHT SIDE: Large Preview ---
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.preview_label = QLabel("No operation performed yet", self)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 2px dashed #aaa; background: #f5f5f5;")
        
        # Lock down the frame layout permanently to completely prevent layout jumping
        self.preview_size = QSize(450, 450)
        self.preview_label.setFixedSize(self.preview_size)
        
        # Keep the locked preview box centered
        right_layout.addStretch()
        right_layout.addWidget(self.preview_label, alignment=Qt.AlignmentFlag.AlignCenter)
        right_layout.addStretch()
        
        # Add components to splitter
        main_splitter.addWidget(left_container)
        main_splitter.addWidget(right_container)
        main_splitter.setStretchFactor(0, 3)
        main_splitter.setStretchFactor(1, 2)
        
        # Add the interactive workbench area to the master layout window
        window_layout.addWidget(main_splitter)
        
        # --- BOTTOM ROW: Dialog Footer Actions (Cancel / Apply) ---
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

    def get_selected_indices(self):
        return [w.index for w in self.image_widgets if w.is_checked()]

    def toggle_select_all(self):
        """Forces all child image widgets to match the target action cleanly."""
        # Check current label text to understand user's contextual intent.
        # If it says "Deselect All", user wants EVERYTHING off, regardless of partial states.
        intent_deselect = (self.master_checkbox.text() == "Deselect All")
        target_state = not intent_deselect
        
        # Block signals on child checkboxes to prevent feedback loop recursion
        for widget in self.image_widgets:
            widget.checkbox.blockSignals(True)
            widget.set_checked(target_state)
            widget.checkbox.blockSignals(False)
        
        # Update Master widget states
        self.master_checkbox.blockSignals(True)
        if target_state:
            self.master_checkbox.setCheckState(Qt.CheckState.Checked)
            self.master_checkbox.setText("Deselect All")
        else:
            self.master_checkbox.setCheckState(Qt.CheckState.Unchecked)
            self.master_checkbox.setText("Select All")
        self.master_checkbox.blockSignals(False)

    def update_master_checkbox_text(self):
        """Monitors individual checks to update the master label and state contextually."""
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
            # If some are selected, label should prompt "Deselect All" to clear the board safely
            self.master_checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
            self.master_checkbox.setText("Deselect All")
            
        self.master_checkbox.blockSignals(False)

    def update_preview(self, pixmap):
        """Displays the resulting image scaled cleanly into the locked placeholder bounds."""
        scaled_pixmap = pixmap.scaled(
            self.preview_size, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.preview_label.setPixmap(scaled_pixmap)

    def compute_mode(self):
        selected_idx = self.get_selected_indices()
        if not selected_idx:
            self.preview_label.setPixmap(QPixmap()) 
            self.preview_label.setText("Please select images first.")
            return
            
        base_pixmap = self.pixmaps[selected_idx[0]]
        result = base_pixmap.copy()
        
        painter = QPainter(result)
        painter.setPen(QColor(0, 0, 255, 180))
        painter.setFont(self.font())
        painter.drawText(result.rect(), Qt.AlignmentFlag.AlignCenter, "MODE RESULT")
        painter.end()
        
        self.update_preview(result)

    def inpaint_selected(self):
        selected_idx = self.get_selected_indices()
        if not selected_idx:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("Please select images first.")
            return
            
        base_pixmap = self.pixmaps[selected_idx[0]]
        result = base_pixmap.copy()
        
        painter = QPainter(result)
        painter.setPen(QColor(255, 0, 0, 180))
        painter.drawText(result.rect(), Qt.AlignmentFlag.AlignCenter, "INPAINTED")
        painter.end()
        
        self.update_preview(result)

# --- Dummy Execution Block ---
def create_dummy_pixmap(width, height, color_name, text):
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor(color_name))
    painter = QPainter(pixmap)
    painter.setPen(Qt.GlobalColor.black if color_name not in ["blue", "red", "magenta"] else Qt.GlobalColor.white)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, f"{text}\n({width}x{height})")
    painter.end()
    return pixmap

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    resolutions = [
        (100, 100), (800, 600), (1920, 1080), (300, 400),
        (500, 500), (128, 128), (200, 600),   (1000, 200),
        (400, 300), (64, 64),   (1200, 1200), (720, 1280)
    ]
    colors = [
        "red", "green", "blue", "yellow", "cyan", "magenta", 
        "orange", "gray", "white", "lightgray", "darkcyan", "darkkhaki"
    ]
    
    dummy_pixmaps = [
        create_dummy_pixmap(resolutions[i][0], resolutions[i][1], colors[i], f"Img {i+1}") 
        for i in range(12)
    ]
    
    dialog = ImageGridModal(dummy_pixmaps)
    
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("User clicked Apply! Selected indices:", dialog.get_selected_indices())
    else:
        print("User cancelled the transaction.")