import sys
import math
import cv2
import numpy as np
from qtpy.QtWidgets import (
    QApplication, QDialog, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QCheckBox, QLabel, QPushButton, QScrollArea, QSplitter, 
    QSlider, QComboBox, QSpinBox, QGroupBox
)
from qtpy.QtGui import QColor, QPainter, QPolygonF, QPen
from qtpy.QtCore import Qt, QSize, QThread, Signal, QPointF
from qt_widgets import NDarray_to_QPixmap

class ComputeWorker(QThread):
    finished = Signal(np.ndarray)
    error = Signal(str)

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
    """Interactive canvas supporting live masks, vector dragging, Ctrl+Wheel zoom, and Middle-Click Panning."""
    zoom_changed = Signal()  # Notify parent window to update status labels

    def __init__(self, base_size, parent=None):
        super().__init__(parent)
        self.base_size = base_size
        self.zoom_factor = 1.0
        self.setFixedSize(self.base_size)
        
        self.base_np = None          
        self.inpainted_np = None     
        self.display_pixmap = None
        self.preview_mode = False    
        
        self.polygons = []
        self.current_mouse_pos = None  
        
        # Dragging/Hover states for vector points
        self.dragged_poly_idx = None
        self.dragged_point_idx = None
        self.hovered_poly_idx = None
        self.hovered_point_idx = None
        self.handle_radius = 6.0      
        
        # Panning states
        self.is_panning = False
        self.pan_start_pos = None

        self.setMouseTracking(True)
        
    def set_image(self, arr, clear_mask=True):
        self.base_np = arr.copy()
        self.update_scaled_pixmap()
        if clear_mask:
            self.clear_mask_data()
        self.update()

    def update_scaled_pixmap(self):
        if self.base_np is None:
            return
        
        active_np = self.inpainted_np if (self.preview_mode and self.inpainted_np is not None) else self.base_np
        raw_pixmap = NDarray_to_QPixmap(active_np)
        
        target_size = QSize(int(self.base_size.width() * self.zoom_factor), 
                            int(self.base_size.height() * self.zoom_factor))
        
        self.display_pixmap = raw_pixmap.scaled(
            target_size, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.setFixedSize(target_size)

    def set_zoom(self, factor, mouse_pos=None):
        """Sets zoom factor and anchors the view around the cursor position."""
        old_factor = self.zoom_factor
        self.zoom_factor = max(0.25, min(15.0, factor))  # Bounds: 25% to 1500%
        
        if old_factor == self.zoom_factor:
            return

        scroll_area = self.get_scroll_area()
        if scroll_area:
            h_bar = scroll_area.horizontalScrollBar()
            v_bar = scroll_area.verticalScrollBar()
            
            anchor = mouse_pos if mouse_pos else QPointF(self.width() / 2, self.height() / 2)
            logical_x = anchor.x() / old_factor
            logical_y = anchor.y() / old_factor
            
            scroll_dx = anchor.x() - h_bar.value()
            scroll_dy = anchor.y() - v_bar.value()

            self.update_scaled_pixmap()

            h_bar.setValue(int(logical_x * self.zoom_factor - scroll_dx))
            v_bar.setValue(int(logical_y * self.zoom_factor - scroll_dy))
        else:
            self.update_scaled_pixmap()
            
        self.zoom_changed.emit()
        self.update()

    def get_scroll_area(self):
        """Helper to find the bounding scroll viewport layout wrapper."""
        parent_widget = self.parent()
        if parent_widget and hasattr(parent_widget, 'parent'):
            grandparent = parent_widget.parent()
            if isinstance(grandparent, QScrollArea):
                return grandparent
        return None

    def clear_mask_data(self):
        self.polygons = []
        self.inpainted_np = None
        self.preview_mode = False
        self.dragged_poly_idx = None
        self.dragged_point_idx = None
        self.hovered_poly_idx = None
        self.hovered_point_idx = None
        self.is_panning = False
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()

    def set_preview_mode(self, show_preview):
        self.preview_mode = show_preview
        self.update_scaled_pixmap()
        self.update()

    def to_logical(self, pos):
        return QPointF(pos.x() / self.zoom_factor, pos.y() / self.zoom_factor)

    def wheelEvent(self, event):
        """Ctrl + Wheel to zoom seamlessly around cursor location."""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            angle = event.angleDelta().y()
            factor = self.zoom_factor * (1.15 if angle > 0 else 0.82)
            self.set_zoom(factor, event.position())
            event.accept()
        else:
            super().wheelEvent(event)

    def _find_hovered_vertex(self, logical_pos):
        scaled_radius = self.handle_radius / self.zoom_factor
        for poly_idx, poly in enumerate(self.polygons):
            for pt_idx, pt in enumerate(poly['points']):
                distance = math.hypot(logical_pos.x() - pt.x(), logical_pos.y() - pt.y())
                if distance <= scaled_radius:
                    return poly_idx, pt_idx
        return None, None

    def mousePressEvent(self, event):
        if self.display_pixmap is None:
            return

        # 1. Capture Panning Initialization (Middle Mouse Button click)
        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = True
            self.pan_start_pos = event.globalPosition()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
            return

        if self.preview_mode:
            return
            
        logical_pos = self.to_logical(event.position())
        
        # 2. Polygon Point Mask Controls
        if event.button() == Qt.MouseButton.LeftButton:
            poly_idx, pt_idx = self._find_hovered_vertex(logical_pos)
            if poly_idx is not None:
                self.dragged_poly_idx = poly_idx
                self.dragged_point_idx = pt_idx
                return
            
            if not self.polygons or self.polygons[-1]['is_closed']:
                self.polygons.append({'points': [logical_pos], 'is_closed': False})
            else:
                self.polygons[-1]['points'].append(logical_pos)
                
            self.inpainted_np = None
            self.update()
            
        elif event.button() == Qt.MouseButton.RightButton:
            if self.polygons and not self.polygons[-1]['is_closed']:
                if len(self.polygons[-1]['points']) >= 3:
                    self.polygons[-1]['is_closed'] = True
                else:
                    self.polygons.pop()
                self.update()

    def mouseMoveEvent(self, event):
        if self.display_pixmap is None:
            return

        # 1. Handle Panning Delta Modifications
        if self.is_panning and self.pan_start_pos is not None:
            current_global_pos = event.globalPosition()
            delta = current_global_pos - self.pan_start_pos
            self.pan_start_pos = current_global_pos
            
            scroll_area = self.get_scroll_area()
            if scroll_area:
                h_bar = scroll_area.horizontalScrollBar()
                v_bar = scroll_area.verticalScrollBar()
                h_bar.setValue(int(h_bar.value() - delta.x()))
                v_bar.setValue(int(v_bar.value() - delta.y()))
            event.accept()
            return

        if self.preview_mode:
            return
            
        logical_pos = self.to_logical(event.position())
        self.current_mouse_pos = logical_pos
        
        # 2. Handle point dragging adjustments
        if self.dragged_poly_idx is not None and self.dragged_point_idx is not None:
            self.polygons[self.dragged_poly_idx]['points'][self.dragged_point_idx] = logical_pos
            self.inpainted_np = None 
            self.update()
            return
            
        # 3. Dynamic Cursor Updates
        p_idx, pt_idx = self._find_hovered_vertex(logical_pos)
        if p_idx != self.hovered_poly_idx or pt_idx != self.hovered_point_idx:
            self.hovered_poly_idx = p_idx
            self.hovered_point_idx = pt_idx
            if self.hovered_point_idx is not None:
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            self.update()
            
        if self.polygons and not self.polygons[-1]['is_closed']:
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.is_panning = False
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
            
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragged_poly_idx = None
            self.dragged_point_idx = None

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.display_pixmap is None:
            painter.setPen(QPen(QColor("#bbb"), 2, Qt.PenStyle.DashLine))
            painter.setBrush(QColor("#fafafa"))
            painter.drawRect(self.rect())
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Workbench Area (Locked until Mode is Computed)")
            return
            
        painter.drawPixmap(0, 0, self.display_pixmap)
        
        if not self.preview_mode and self.polygons:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            painter.save()
            painter.scale(self.zoom_factor, self.zoom_factor)
            
            line_thickness = 2.0 / self.zoom_factor
            dash_thickness = 1.0 / self.zoom_factor
            
            for poly in self.polygons:
                pts = poly['points']
                if poly['is_closed']:
                    painter.setPen(QPen(QColor(255, 0, 0, 200), line_thickness))
                    painter.setBrush(QColor(255, 0, 0, 60))
                    painter.drawPolygon(QPolygonF(pts))
                else:
                    painter.setPen(QPen(QColor(0, 120, 255), line_thickness))
                    for i in range(len(pts) - 1):
                        painter.drawLine(pts[i], pts[i+1])
                    if self.current_mouse_pos is not None and poly == self.polygons[-1]:
                        painter.setPen(QPen(QColor(0, 120, 255, 140), dash_thickness, Qt.PenStyle.DashLine))
                        painter.drawLine(pts[-1], self.current_mouse_pos)
            
            for poly_idx, poly in enumerate(self.polygons):
                for pt_idx, pt in enumerate(poly['points']):
                    if poly_idx == self.hovered_poly_idx and pt_idx == self.hovered_point_idx:
                        painter.setBrush(QColor(255, 69, 0)) 
                        r = (self.handle_radius + 1) / self.zoom_factor
                    else:
                        painter.setBrush(QColor(255, 215, 0)) 
                        r = (self.handle_radius - 2) / self.zoom_factor
                    painter.setPen(QPen(Qt.GlobalColor.black, 1.0 / self.zoom_factor))
                    painter.drawEllipse(pt, r, r)
                    
            painter.restore()

    def flatten_mask(self):
        if self.base_np is None or not self.polygons:
            return None
            
        h, w, _ = self.base_np.shape
        scale_w = w / self.base_size.width()
        scale_h = h / self.base_size.height()
        
        mask = np.zeros((h, w), dtype=np.uint8)
        has_content = False
        
        for poly in self.polygons:
            if not poly['is_closed'] or len(poly['points']) < 3:
                continue
                
            mapped_points = []
            for pt in poly['points']:
                orig_x = pt.x() * scale_w
                orig_y = pt.y() * scale_h
                mapped_points.append([orig_x, orig_y])
                
            pts_array = np.array(mapped_points, dtype=np.int32).reshape((-1, 1, 2))
            cv2.fillPoly(mask, [pts_array], 255)
            has_content = True
            
        return mask if has_content else None


class ImageItemWidget(QWidget):
    def __init__(self, np_array, index, thumb_size=240, parent=None):
        super().__init__(parent)
        self.index = index
        self.np_array = np_array
        self.base_pixmap = NDarray_to_QPixmap(self.np_array)
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


class BackgroundModal(QDialog):
    def __init__(self, np_arrays, parent=None):
        super().__init__(parent)
        self.np_arrays = np_arrays  
        self.image_widgets = []
        self.processed_result_np = None  
        self.worker = None 
        self.current_thumb_size = 200 
        
        self.setWindowTitle("Background Manager")
        self.resize(1300, 850)
        self.init_ui()
        self.update_workflow_state()
        
    def init_ui(self):
        window_layout = QVBoxLayout(self)
        
        self.status_banner = QLabel(self)
        self.status_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_banner.setStyleSheet("font-size: 14px; font-weight: bold; padding: 2px; background-color: #eaeaea; border-radius: 4px; color: #333;")
        self.status_banner.setMaximumHeight(32)
        window_layout.addWidget(self.status_banner)
        
        main_splitter = QSplitter(Qt.Orientation.Horizontal, self)
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
        
        self.right_container = QWidget()
        right_layout = QVBoxLayout(self.right_container)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        # --- ZOOMABLE AREA WRAPPER ---
        self.canvas_scroll_area = QScrollArea(self)
        self.canvas_scroll_area.setWidgetResizable(False)
        self.canvas_scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        #self.canvas_scroll_area.setStyleSheet("background-color: #333; border: 1px solid #111;")
        
        self.preview_size = QSize(512, 512)
        self.canvas_widget = DrawPolyMask(self.preview_size, self)
        self.canvas_widget.zoom_changed.connect(self.update_workflow_state)
        self.canvas_scroll_area.setWidget(self.canvas_widget)
        right_layout.addWidget(self.canvas_scroll_area, 1)
        
        # Minimalist Navigation Controls Row
        zoom_ctrl_layout = QHBoxLayout()
        self.lbl_zoom = QLabel("Zoom: 100%", self)
        btn_zoom_reset = QPushButton("Reset View (100%)", self)
        btn_zoom_reset.clicked.connect(lambda: self.canvas_widget.set_zoom(1.0))
        
        zoom_ctrl_layout.addWidget(self.lbl_zoom)
        zoom_ctrl_layout.addWidget(btn_zoom_reset)
        zoom_ctrl_layout.addStretch()
        right_layout.addLayout(zoom_ctrl_layout)
        
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
        self.btn_clear_mask = QPushButton("Clear Masks", self)
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
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 1)
        window_layout.addWidget(main_splitter)
        
        footer_layout = QHBoxLayout()
        footer_layout.addStretch() 
        self.btn_cancel = QPushButton("Cancel", self)
        self.btn_apply = QPushButton("Step 4: Apply", self)
        self.btn_apply.setStyleSheet("font-weight: bold; padding: 4px 15px;")
        self.btn_apply.setDefault(True) 
        
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_apply.clicked.connect(self.accept)
        
        footer_layout.addWidget(self.btn_cancel)
        footer_layout.addWidget(self.btn_apply)
        window_layout.addLayout(footer_layout)

    def update_workflow_state(self):
        selected_count = len(self.get_selected_indices())
        self.lbl_zoom.setText(f"Zoom: {int(self.canvas_widget.zoom_factor * 100)}%")
        
        if selected_count == 0:
            self.status_banner.setText("STEP 1: Please select one or more image thumbnails on the grid.")
            self.status_banner.setStyleSheet("font-size: 14px; font-weight: bold; padding: 2px; background-color: #fff3cd; border-radius: 4px; color: #856404;")
            self.btn_mode.setEnabled(False)
            self.right_container.setEnabled(False)
            self.btn_apply.setEnabled(False)
            return

        if self.processed_result_np is None:
            self.status_banner.setText("STEP 2: Click 'Compute Mode' to extract the background.")
            self.status_banner.setStyleSheet("font-size: 14px; font-weight: bold; padding: 2px; background-color: #cce5ff; border-radius: 4px; color: #004085;")
            self.btn_mode.setEnabled(True)
            self.btn_mode.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; padding: 6px 12px;")
            self.right_container.setEnabled(False)
            self.btn_apply.setEnabled(False)
            return

        self.btn_mode.setEnabled(True)
        self.btn_mode.setStyleSheet("font-weight: normal;")
        self.right_container.setEnabled(True)
        self.btn_apply.setEnabled(True)
        self.btn_apply.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 4px 15px;")
        
        if self.canvas_widget.inpainted_np is not None:
            self.status_banner.setText("STEP 4 COMPLETE: Inpaint generated. Press 'Apply' to save and close.")
            self.status_banner.setStyleSheet("font-size: 14px; font-weight: bold; padding: 2px; background-color: #d4edda; border-radius: 4px; color: #155724;")
        else:
            self.status_banner.setText("NAVIGATION: [Ctrl+Wheel] Zoom. [Middle Click Drag] Pan around canvas.")
            self.status_banner.setStyleSheet("font-size: 14px; font-weight: bold; padding: 2px; background-color: #e2e3e5; border-radius: 4px; color: #383d41;")

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
    dummy_np_arrays = [create_dummy_np_array(1200, 1200, colors[i], pattern_offset=i*8) for i in range(12)]
    
    dialog = BackgroundModal(dummy_np_arrays)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        print("Modal Closed Successfully.")