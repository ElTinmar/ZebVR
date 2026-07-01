import sys
import math
from numpy.typing import NDArray
from qtpy.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QLabel, QGraphicsItem, QGraphicsView, 
                            QGraphicsScene, QFrame, QPushButton, QListWidget, QFileDialog)
from qtpy.QtGui import QColor, QPen, QBrush, QPainter, QPainterPath, QPainterPathStroker, QPixmap, QFont, QMouseEvent
from qtpy.QtCore import Qt, QRectF, QPointF, Signal as pyqtSignal
from qt_widgets import NDarray_to_QPixmap


class BaseSystemHandle(QGraphicsItem):
    def __init__(self, color: QColor, size: float, interaction_margin: float = 10.0, parent=None):
        super().__init__(parent)
        self.color = color
        self.size = size
        self.interaction_margin = interaction_margin
        self._hovered = False
        
        self.setAcceptHoverEvents(True)
        self.setFlags(QGraphicsItem.ItemSendsGeometryChanges)
        
        self._drag_start_scene = QPointF()
        self._drag_start_parent_pos = QPointF()
        self._drag_start_local_mouse = QPointF()

    def boundingRect(self):
        s = self.size + self.interaction_margin
        return QRectF(-s, -s, s * 2, s * 2)

    def shape(self):
        path = QPainterPath()
        s = self.size + self.interaction_margin
        path.addEllipse(QRectF(-s, -s, s * 2, s * 2))
        return path

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.unsetCursor()
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_scene = event.scenePos()
            parent = self.parentItem()
            if parent:
                self._drag_start_parent_pos = parent.pos()
                self._drag_start_local_mouse = parent.mapFromScene(event.scenePos())
            event.accept()
        else:
            super().mousePressEvent(event)


class OriginHandle(BaseSystemHandle):
    def __init__(self, color: QColor, parent=None):
        super().__init__(color, size=14, interaction_margin=10, parent=parent)

    def hoverEnterEvent(self, event):
        self.setCursor(Qt.CrossCursor)
        super().hoverEnterEvent(event)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        fill = self.color.lighter(130) if self._hovered else self.color
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(fill))
        
        r = self.size / 2
        painter.drawEllipse(QPointF(0, 0), r, r)
        
        alpha = 140 if self._hovered else 90
        painter.setPen(QPen(QColor(0, 0, 0, alpha), 1.2))
        painter.drawLine(QPointF(-r * 1.5, 0), QPointF(r * 1.5, 0))
        painter.drawLine(QPointF(0, -r * 1.5), QPointF(0, r * 1.5))

    def mouseMoveEvent(self, event):
        parent = self.parentItem()
        if parent and event.buttons() & Qt.LeftButton:
            delta = event.scenePos() - self._drag_start_scene
            parent.setPos(self._drag_start_parent_pos + delta)
            parent.parent_widget.notify_system_changed(parent)
            event.accept()


class AxisHandle(BaseSystemHandle):
    def __init__(self, color: QColor, parent=None):
        super().__init__(color, size=10, interaction_margin=10, parent=parent)

    def hoverEnterEvent(self, event):
        self.setCursor(Qt.SizeAllCursor)
        super().hoverEnterEvent(event)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        fill = self.color.lighter(130) if self._hovered else self.color
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(fill))
        painter.drawEllipse(QPointF(0, 0), self.size / 2, self.size / 2)

    def mouseMoveEvent(self, event):
        parent = self.parentItem()
        if parent and event.buttons() & Qt.LeftButton:
            local_mouse_pos = parent.mapFromScene(event.scenePos())
            parent.handle_axis_drag(self, local_mouse_pos)
            event.accept()


class BBoxCornerHandle(BaseSystemHandle):
    def __init__(self, color: QColor, corner_id: str, parent=None):
        super().__init__(color, size=8, interaction_margin=10, parent=parent)
        self.corner_id = corner_id

    def hoverEnterEvent(self, event):
        self.setCursor(Qt.SizeFDiagCursor if self.corner_id in ["tl", "br"] else Qt.SizeBDiagCursor)
        super().hoverEnterEvent(event)

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        fill = self.color.lighter(130) if self._hovered else self.color
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(fill))
        r = self.size / 2
        painter.drawRect(QRectF(-r, -r, self.size, self.size))

    def mouseMoveEvent(self, event):
        parent = self.parentItem()
        if parent and event.buttons() & Qt.LeftButton:
            local_mouse_pos = parent.mapFromScene(event.scenePos())
            parent.handle_bbox_resize(self, local_mouse_pos)
            event.accept()


class InteractiveCoordinateSystem(QGraphicsItem):
    def __init__(self, index: int, initial_pos: QPointF, parent_widget):
        super().__init__()
        self.index: int = index  
        self.parent_widget = parent_widget
        self.axes_visible: bool = True  
        
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setPos(initial_pos)

        self._len_lateral = 75.0
        self._len_heading = 150.0
        self._current_angle = 0.0

        self._bbox_w = 200.0
        self._bbox_h = 200.0
        self._bbox_cx = 0.0
        self._bbox_cy = 0.0

        self.color_origin = QColor(255, 255, 255, 180) 
        self.color_lateral = QColor(230, 159, 0)        
        self.color_heading = QColor(86, 180, 233)       
        self.color_bbox = QColor(255, 255, 255, 160)

        # Child handles initialization
        self.origin = OriginHandle(self.color_origin, parent=self)
        self.origin.setPos(0, 0)

        self.axis_lateral = AxisHandle(self.color_lateral, parent=self)
        self.axis_heading = AxisHandle(self.color_heading, parent=self)
        
        self.bbox_tl = BBoxCornerHandle(self.color_bbox, "tl", parent=self)
        self.bbox_tr = BBoxCornerHandle(self.color_bbox, "tr", parent=self)
        self.bbox_bl = BBoxCornerHandle(self.color_bbox, "bl", parent=self)
        self.bbox_br = BBoxCornerHandle(self.color_bbox, "br", parent=self)

        self.update_axis_positions()
        self.update_bbox_positions()

    def set_axes_visible(self, visible: bool):
        self.prepareGeometryChange()
        self.axes_visible = visible
        self.axis_lateral.setVisible(visible)
        self.axis_heading.setVisible(visible)

        if not self.axes_visible:
            # Shift the coordinate pivot system directly onto the physical box layout center coordinates
            scene_center = self.mapToScene(QPointF(self._bbox_cx, self._bbox_cy))
            self.setPos(scene_center)
            self._bbox_cx = 0.0
            self._bbox_cy = 0.0
            
        self.update_bbox_positions()
        self.update()

    def update_axis_positions(self):
        x_target = QPointF(math.cos(self._current_angle) * self._len_lateral, 
                           math.sin(self._current_angle) * self._len_lateral)
        self.axis_lateral.setPos(x_target)
        
        y_angle = self._current_angle - (math.pi / 2.0)
        y_target = QPointF(math.cos(y_angle) * self._len_heading, 
                           math.sin(y_angle) * self._len_heading)
        self.axis_heading.setPos(y_target)

    def update_bbox_positions(self):
        hw, hh = self._bbox_w / 2.0, self._bbox_h / 2.0
        self.bbox_tl.setPos(self._bbox_cx - hw, self._bbox_cy - hh)
        self.bbox_tr.setPos(self._bbox_cx + hw, self._bbox_cy - hh)
        self.bbox_bl.setPos(self._bbox_cx - hw, self._bbox_cy + hh)
        self.bbox_br.setPos(self._bbox_cx + hw, self._bbox_cy + hh)

    def get_bbox_rect(self):
        return QRectF(self._bbox_cx - self._bbox_w / 2.0, 
                      self._bbox_cy - self._bbox_h / 2.0, 
                      self._bbox_w, self._bbox_h)

    def boundingRect(self):
        bbox = self.get_bbox_rect()
        if not self.axes_visible:
            return bbox.united(self.origin.boundingRect()).adjusted(-15, -15, 15, 15)
        axes_rect = QRectF(self.origin.pos(), self.axis_lateral.pos()).united(QRectF(self.origin.pos(), self.axis_heading.pos()))
        return bbox.united(axes_rect).adjusted(-35, -20, 20, 35)

    def shape(self):
        path = QPainterPath()
        if self.axes_visible:
            path.moveTo(self.origin.pos())
            path.lineTo(self.axis_lateral.pos())
            path.moveTo(self.origin.pos())
            path.lineTo(self.axis_heading.pos())
        path.addRect(self.get_bbox_rect())
        
        stroker = QPainterPathStroker()
        stroker.setWidth(16)
        stroker.setCapStyle(Qt.RoundCap)
        total_shape = stroker.createStroke(path)
        
        total_shape.addPath(self.origin.mapToParent(self.origin.shape()))
        if self.axes_visible:
            total_shape.addPath(self.axis_lateral.mapToParent(self.axis_lateral.shape()))
            total_shape.addPath(self.axis_heading.mapToParent(self.axis_heading.shape()))
            
        total_shape.addPath(self.bbox_tl.mapToParent(self.bbox_tl.shape()))
        total_shape.addPath(self.bbox_tr.mapToParent(self.bbox_tr.shape()))
        total_shape.addPath(self.bbox_bl.mapToParent(self.bbox_bl.shape()))
        total_shape.addPath(self.bbox_br.mapToParent(self.bbox_br.shape()))
        return total_shape

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.setPen(QPen(self.color_bbox, 2.0, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.get_bbox_rect())

        if self.axes_visible:
            painter.setPen(QPen(QColor(self.color_lateral.red(), self.color_lateral.green(), self.color_lateral.blue(), 230), 3.0))
            painter.drawLine(self.origin.pos(), self.axis_lateral.pos())
            
            painter.setPen(QPen(QColor(self.color_heading.red(), self.color_heading.green(), self.color_heading.blue(), 230), 3.0))
            painter.drawLine(self.origin.pos(), self.axis_heading.pos())

        label = str(self.index)
        font = QFont("Arial", 12, QFont.Bold)
        painter.setFont(font)
        
        rect_offset = QRectF(-24, 10, 20, 20) if self.axes_visible else QRectF(self._bbox_cx - (self._bbox_w/2.0) + 5, self._bbox_cy - (self._bbox_h/2.0) + 5, 20, 20)
        align_flags = (Qt.AlignRight | Qt.AlignTop) if self.axes_visible else (Qt.AlignLeft | Qt.AlignTop)

        painter.setPen(QColor(0, 0, 0, 255))
        painter.drawText(rect_offset.translated(1, 1), align_flags, label)
        painter.drawText(rect_offset.translated(-1, -1), align_flags, label)

        painter.setPen(QColor(255, 255, 255, 240))
        painter.drawText(rect_offset, align_flags, label)

    def handle_axis_drag(self, node, local_mouse_pos):
        self.prepareGeometryChange()
        dx, dy = local_mouse_pos.x(), local_mouse_pos.y()
        if node == self.axis_lateral:
            self._current_angle = math.atan2(dy, dx)
        elif node == self.axis_heading:
            self._current_angle = math.atan2(dy, dx) + (math.pi / 2.0)
        self.update_axis_positions()
        self.update()
        self.parent_widget.notify_system_changed(self)

    def handle_bbox_resize(self, node, local_mouse_pos):
        self.prepareGeometryChange()
        
        if self.axes_visible:
            self._resize_asymmetric(node, local_mouse_pos)
        else:
            self._resize_symmetric(local_mouse_pos)

        self.update_bbox_positions()
        self.update()
        self.parent_widget.notify_system_changed(self)

    def _resize_asymmetric(self, node, local_mouse_pos):
        """Mode A: Bounding box adjusts freely around a static origin local coordinate point."""
        hw, hh = self._bbox_w / 2.0, self._bbox_h / 2.0
        x1, x2 = self._bbox_cx - hw, self._bbox_cx + hw  
        y1, y2 = self._bbox_cy - hh, self._bbox_cy + hh  

        if "br" in node.corner_id:
            x2, y2 = max(0.0, local_mouse_pos.x()), max(0.0, local_mouse_pos.y())
        elif "tl" in node.corner_id:
            x1, y1 = min(0.0, local_mouse_pos.x()), min(0.0, local_mouse_pos.y())
        elif "tr" in node.corner_id:
            x2, y1 = max(0.0, local_mouse_pos.x()), min(0.0, local_mouse_pos.y())
        elif "bl" in node.corner_id:
            x1, y2 = min(0.0, local_mouse_pos.x()), max(0.0, local_mouse_pos.y())

        self._bbox_w = max(20.0, x2 - x1)
        self._bbox_h = max(20.0, y2 - y1)
        self._bbox_cx = x1 + self._bbox_w / 2.0
        self._bbox_cy = y1 + self._bbox_h / 2.0

    def _resize_symmetric(self, local_mouse_pos):
        """Mode B: Pure uniform resize anchored strictly to the lock center point (0,0)."""
        self._bbox_w = max(20.0, abs(local_mouse_pos.x()) * 2.0)
        self._bbox_h = max(20.0, abs(local_mouse_pos.y()) * 2.0)
        self._bbox_cx = 0.0
        self._bbox_cy = 0.0

    def get_data(self) -> dict:
        bbox_tl_scene_pos = self.mapToScene(self.bbox_tl.pos())
    
        x = bbox_tl_scene_pos.x()
        y = bbox_tl_scene_pos.y()
        w = self._bbox_w
        h = self._bbox_h

        heading_y = self.axis_heading.y() - self.origin.y()
        heading_x = self.axis_heading.x() - self.origin.x()
        lateral_y = self.axis_lateral.y() - self.origin.y()
        lateral_x = self.axis_lateral.x() - self.origin.x()

        offset_x = -self.bbox_tl.x()
        offset_y = -self.bbox_tl.y()

        return {
            "bbox_rect": [x, y, w, h],
            "centroid": [offset_x, offset_y],
            "axes": [
                [heading_x/self._len_heading, lateral_x/self._len_lateral],
                [heading_y/self._len_heading, lateral_y/self._len_lateral]
            ]
        }
    
    def set_data(self, data: dict):
        self.prepareGeometryChange()
        
        x, y, w, h = data["bbox_rect"]
        offset_x, offset_y = data["centroid"]
        
        self._bbox_w = w
        self._bbox_h = h
        
        hw, hh = w / 2.0, h / 2.0
        self._bbox_cx = hw - offset_x
        self._bbox_cy = hh - offset_y
        
        self.setPos(QPointF(x + offset_x, y + offset_y))
        
        axes = data["axes"]
        lateral_x_norm = axes[0][1]
        lateral_y_norm = axes[1][1]
        self._current_angle = math.atan2(lateral_y_norm, lateral_x_norm)
        
        self.update_axis_positions()
        self.update_bbox_positions()
        self.update()


class MultiCoordViewer(QGraphicsView):
    system_updated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor(40, 40, 40)))
        
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        self.coordinate_systems = [] 
        self.bg_pixmap_item = None
        self._global_axes_visible = True

    def toggle_axes_visibility(self):
        self._global_axes_visible = not self._global_axes_visible
        for sys_item in self.coordinate_systems:
            sys_item.set_axes_visible(self._global_axes_visible)
            self.notify_system_changed(sys_item)
        return self._global_axes_visible

    def wheelEvent(self, event):
        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor
        self.scale(zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor, 
                   zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor)
        event.accept()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton:
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            fake_event = QMouseEvent(event.type(), event.position(), Qt.LeftButton, 
                                     event.buttons() | Qt.LeftButton, event.modifiers())
            super().mousePressEvent(fake_event)
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton:
            fake_event = QMouseEvent(event.type(), event.position(), Qt.LeftButton, 
                                     event.buttons() & ~Qt.LeftButton, event.modifiers())
            super().mouseReleaseEvent(fake_event)
            self.setDragMode(QGraphicsView.NoDrag)
        else:
            super().mouseReleaseEvent(event)

    def set_background_image(self, image: NDArray):
        pixmap = NDarray_to_QPixmap(image)
        if self.bg_pixmap_item in self.scene.items(): 
            self.scene.removeItem(self.bg_pixmap_item)
        self.bg_pixmap_item = self.scene.addPixmap(pixmap)
        self.bg_pixmap_item.setZValue(-100)
        self.setSceneRect(QRectF(pixmap.rect()))

    def add_coordinate_system(self, scene_pos: QPointF):
        index = len(self.coordinate_systems)
        coord_sys = InteractiveCoordinateSystem(index, scene_pos, self)
        coord_sys.set_axes_visible(self._global_axes_visible)
        self.scene.addItem(coord_sys)
        self.coordinate_systems.append(coord_sys)
        self.notify_system_changed(coord_sys)

    def remove_coordinate_system(self, index: int):
        if 0 <= index < len(self.coordinate_systems):
            item = self.coordinate_systems.pop(index)
            self.scene.removeItem(item)
            self.reindex_systems()

    def clear_coordinate_systems(self):
        for sys_item in self.coordinate_systems:
            self.scene.removeItem(sys_item)
        self.coordinate_systems.clear()

    def reindex_systems(self):
        for idx, sys_item in enumerate(self.coordinate_systems):
            sys_item.index = idx
            sys_item.update() 
            self.notify_system_changed(sys_item)
        self.scene.update()

    def notify_system_changed(self, system: InteractiveCoordinateSystem):
        self.system_updated.emit(system.get_data())

    def get_data(self) -> dict:
        data = {}
        for idx, sys_item in enumerate(self.coordinate_systems):
            data[idx] = sys_item.get_data()
        return data
    
    def set_data(self, data: dict):
        self.clear_coordinate_systems()
        
        for str_idx in sorted(data.keys(), key=int):
            idx = int(str_idx)
            item_data = data[str_idx]
            
            # Extract temporary scene position to instantiate the object
            x, y, _, _ = item_data["bbox_rect"]
            offset_x, offset_y = item_data["centroid"]
            initial_pos = QPointF(x + offset_x, y + offset_y)
            
            # Create, configure, and add to tracking
            coord_sys = InteractiveCoordinateSystem(idx, initial_pos, self)
            coord_sys.set_axes_visible(self._global_axes_visible)
            coord_sys.set_data(item_data)
            
            self.scene.addItem(coord_sys)
            self.coordinate_systems.append(coord_sys)
            
        self.scene.update()


class MainApplication(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unified Index Image Workspace")
        self.resize(1200, 750)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        
        self.viewer = MultiCoordViewer()
        self.viewer.setSceneRect(0, 0, 1000, 1000)
        self.viewer.system_updated.connect(self.update_telemetry_display)
        main_layout.addWidget(self.viewer, stretch=3)
        
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        main_layout.addWidget(control_panel, stretch=1)
        
        self.load_img_btn = QPushButton("📷 Load Background Image")
        self.load_img_btn.setStyleSheet("font-weight: bold; background-color: #2b5c8f; color: white; padding: 6px;")
        self.load_img_btn.clicked.connect(self.open_image_dialog)
        control_layout.addWidget(self.load_img_btn)
        
        control_layout.addSpacing(10)

        self.toggle_axes_btn = QPushButton("👁️ Toggle Coordinate Axes: ON")
        self.toggle_axes_btn.setStyleSheet("font-weight: bold; background-color: #2ca02c; color: white; padding: 5px;")
        self.toggle_axes_btn.clicked.connect(self.fire_axes_toggle)
        control_layout.addWidget(self.toggle_axes_btn)
        
        control_layout.addSpacing(5)
        
        self.add_btn = QPushButton("Add Bounding Box Set")
        self.add_btn.clicked.connect(self.spawn_system)
        control_layout.addWidget(self.add_btn)
        
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.delete_selected_system)
        control_layout.addWidget(self.remove_btn)
        
        control_layout.addWidget(QLabel("Systems Active Registry:"))
        self.system_list = QListWidget()
        control_layout.addWidget(self.system_list)
        
        control_layout.addWidget(QLabel("Live System Metrics:"))
        self.telemetry_label = QLabel("Interact with or select a system map.")
        self.telemetry_label.setWordWrap(True)
        self.telemetry_label.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.telemetry_label.setStyleSheet(
            "font-family: monospace; font-size: 11px; padding: 8px; background: #1e1e1e; color: #56B4E9;"
        )
        control_layout.addWidget(self.telemetry_label)

        self.spawn_system()

    def open_image_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Background Image Asset", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path: self.viewer.load_background_image(file_path)

    def fire_axes_toggle(self):
        is_visible = self.viewer.toggle_axes_visibility()
        if is_visible:
            self.toggle_axes_btn.setText("👁️ Toggle Coordinate Axes: ON")
            self.toggle_axes_btn.setStyleSheet("font-weight: bold; background-color: #2ca02c; color: white; padding: 5px;")
        else:
            self.toggle_axes_btn.setText("🙈 Toggle Coordinate Axes: OFF")
            self.toggle_axes_btn.setStyleSheet("font-weight: bold; background-color: #d62728; color: white; padding: 5px;")

    def spawn_system(self):
        center_view = self.viewer.viewport().rect().center()
        scene_pt = self.viewer.mapToScene(center_view)
        idx = self.system_list.count()
        scene_pt += QPointF(idx * 45, idx * 45)
        
        self.viewer.add_coordinate_system(scene_pt)
        self.refresh_list_widget()

    def delete_selected_system(self):
        row = self.system_list.currentRow()
        if row >= 0:
            self.viewer.remove_coordinate_system(row)
            self.refresh_list_widget()
            self.telemetry_label.setText("System cleared.")

    def refresh_list_widget(self):
        self.system_list.clear()
        for sys_item in self.viewer.coordinate_systems:
            self.system_list.addItem(f"Bounding Box Set #{sys_item.index}")

    def update_telemetry_display(self, data: dict):
        text = (
            f"BBox      : {data['bbox_rect']} px\n"
            f"Centroid  : {data['centroid']} px\n"
            f"Axes      : {data['axes']}\n"
            f"Navigation  : Wheel = Zoom | Middle-Click = Pan"
        )
        self.telemetry_label.setText(text)
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainApplication()
    win.show()
    sys.exit(app.exec_())