import math
from numpy.typing import NDArray
from qtpy.QtWidgets import (
    QGraphicsItem, 
    QGraphicsView, 
    QGraphicsObject,
    QGraphicsScene
)
from qtpy.QtGui import (
    QColor, 
    QPen, 
    QBrush, 
    QPainter, 
    QPainterPath, 
    QPainterPathStroker, 
    QFont, 
    QMouseEvent
)
from qtpy.QtCore import (
    Qt, 
    QRectF, 
    QPointF, 
    Signal
)
from qt_widgets import NDarray_to_QPixmap

class ScaleInvariantLabel(QGraphicsObject):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.text = text
        self.setFlags(QGraphicsItem.ItemIgnoresTransformations)
        self.font = QFont("Arial", 14, QFont.Bold)

    def boundingRect(self):
        return QRectF(-50, -50, 100, 100)

    def shape(self):
        path = QPainterPath()
        path.addRect(self.boundingRect())
        return path

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setFont(self.font)
    
        offset_x = 10
        offset_y = 20
        
        painter.setPen(QColor(0, 0, 0, 255))
        painter.drawText(offset_x + 1, offset_y + 1, self.text)
        painter.drawText(offset_x - 1, offset_y - 1, self.text)
        
        painter.setPen(QColor(255, 255, 255, 240))
        painter.drawText(offset_x, offset_y, self.text)

class ROIButton(QGraphicsObject):
    clicked = Signal()

    def __init__(self, text: str, bg_color: QColor, hover_color: QColor, pixel_offset: QPointF, parent=None):
        super().__init__(parent)
        self.text = text
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.pixel_offset = pixel_offset  # Store fixed screen pixel offset
        self._hovered = False
        
        self.setFlags(QGraphicsItem.ItemIgnoresTransformations)
        self.setAcceptHoverEvents(True)

    def boundingRect(self):
        # Shift the interaction bounding box by the fixed pixel offset
        return QRectF(-12 + self.pixel_offset.x(), -12 + self.pixel_offset.y(), 24, 24)

    def shape(self):
        path = QPainterPath()
        path.addEllipse(self.boundingRect())
        return path

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        
        color = self.hover_color if self._hovered else self.bg_color
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color))
        
        # Draw explicitly at the offset location
        painter.drawEllipse(self.boundingRect())
        
        painter.setPen(QColor(255, 255, 255, 220))
        painter.setFont(QFont("Arial", 14, QFont.Bold))
        rect = self.boundingRect().adjusted(0, -1, 0, 0)
        painter.drawText(rect, Qt.AlignCenter, self.text)

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.setCursor(Qt.PointingHandCursor)
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.unsetCursor()
        self.update()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.boundingRect().contains(event.pos()):
            self.clicked.emit()
            event.accept()
        else:
            super().mouseReleaseEvent(event)
            
class BaseSystemHandle(QGraphicsObject):
    state_changed = Signal()
    selected_signal = Signal()
    
    def __init__(self, color: QColor, size: float, interaction_margin: float = 10.0, parent=None):
        super().__init__(parent)
        self.color = color
        self.size = size
        self.interaction_margin = interaction_margin
        self._hovered = False
        
        self.setAcceptHoverEvents(True)
        self.setFlags(QGraphicsItem.ItemSendsGeometryChanges | QGraphicsItem.ItemIgnoresTransformations)
        
        self._drag_start_scene = QPointF()
        self._drag_start_parent_pos = QPointF()

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
        # Ignore handle manipulation if locked
        if self.parentItem() and getattr(self.parentItem(), "is_locked", False):
            event.ignore()
            return
            
        if event.button() == Qt.LeftButton:
            self._drag_start_scene = event.scenePos()
            self.selected_signal.emit()

            parent = self.parentItem()
            if parent:
                self._drag_start_parent_pos = parent.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.state_changed.emit()
        super().mouseReleaseEvent(event)


class OriginHandle(BaseSystemHandle):
    def __init__(self, color: QColor, parent=None):
        super().__init__(color, size=14, interaction_margin=10, parent=parent)

    def hoverEnterEvent(self, event):
        if not getattr(self.parentItem(), "is_locked", False):
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
        crosshair_pen = QPen(QColor(0, 0, 0, alpha), 1.2)
        crosshair_pen.setCosmetic(True)
        painter.setPen(crosshair_pen)
        painter.drawLine(QPointF(-r * 1.5, 0), QPointF(r * 1.5, 0))
        painter.drawLine(QPointF(0, -r * 1.5), QPointF(0, r * 1.5))

    def mouseMoveEvent(self, event):
        parent = self.parentItem()
        scene = self.scene()

        if parent and scene and (event.buttons() & Qt.LeftButton) and not parent.is_locked:
            delta = event.scenePos() - self._drag_start_scene
            parent.handle_origin_move(delta, self._drag_start_parent_pos)
            event.accept()


class AxisHandle(BaseSystemHandle):
    def __init__(self, color: QColor, parent=None):
        super().__init__(color, size=10, interaction_margin=10, parent=parent)

    def hoverEnterEvent(self, event):
        if not getattr(self.parentItem(), "is_locked", False):
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
        if parent and (event.buttons() & Qt.LeftButton) and not parent.is_locked:
            local_mouse_pos = parent.mapFromScene(event.scenePos())
            parent.handle_axis_drag(self, local_mouse_pos)
            event.accept()


class BBoxCornerHandle(BaseSystemHandle):
    def __init__(self, color: QColor, corner_id: str, parent=None):
        super().__init__(color, size=8, interaction_margin=10, parent=parent)
        self.corner_id = corner_id

    def hoverEnterEvent(self, event):
        if not getattr(self.parentItem(), "is_locked", False):
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
        if parent and (event.buttons() & Qt.LeftButton) and not parent.is_locked:
            local_mouse_pos = parent.mapFromScene(event.scenePos())
            parent.handle_bbox_resize(self, local_mouse_pos)
            event.accept()


class InteractiveCoordinateSystem(QGraphicsObject):
    state_changed = Signal()
    selected_signal = Signal(int)

    def __init__(self, index: int, initial_pos: QPointF, parent_widget):
        super().__init__()
        self.index: int = index  
        self.parent_widget = parent_widget
        self.axes_visible: bool = True  
        self.is_locked: bool = False
        
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemSendsGeometryChanges)
        self.setAcceptHoverEvents(True)
        self.setPos(initial_pos)

        self._len_lateral = 75.0
        self._len_heading = 150.0
        self._current_angle = 0.0

        self._bbox_w = 200.0
        self._bbox_h = 200.0
        self._bbox_cx = 0.0
        self._bbox_cy = 0.0

        self._drag_start_scene = QPointF()
        self._drag_start_pos = QPointF()

        self.color_origin = QColor(255, 255, 255, 180) 
        self.color_lateral = QColor(230, 159, 0)        
        self.color_heading = QColor(204, 121, 167)       
        self.color_bbox = QColor(255, 255, 255, 160)
        self.color_bbox_selected = QColor(0, 122, 255, 220)  

        self.origin = OriginHandle(self.color_origin, parent=self)
        self.origin.setPos(0, 0)

        self.axis_lateral = AxisHandle(self.color_lateral, parent=self)
        self.axis_heading = AxisHandle(self.color_heading, parent=self)
        
        self.bbox_tl = BBoxCornerHandle(self.color_bbox, "tl", parent=self)
        self.bbox_tr = BBoxCornerHandle(self.color_bbox, "tr", parent=self)
        self.bbox_bl = BBoxCornerHandle(self.color_bbox, "bl", parent=self)
        self.bbox_br = BBoxCornerHandle(self.color_bbox, "br", parent=self)

        self.btn_delete = ROIButton("×", QColor(190, 50, 50, 180), QColor(240, 40, 40, 240), 
                                    pixel_offset=QPointF(-16, 16), parent=self.bbox_tr)
                                    
        self.btn_lock = ROIButton("🔓", QColor(60, 60, 60, 180), QColor(100, 100, 100, 240), 
                                  pixel_offset=QPointF(-46, 16), parent=self.bbox_tr)

        self.label_item = ScaleInvariantLabel(str(self.index), parent=self)

        # Wire Up Button actions
        self.btn_delete.clicked.connect(self._on_delete_clicked)
        self.btn_lock.clicked.connect(self.toggle_lock)

        self.origin.state_changed.connect(self.state_changed.emit)
        self.axis_lateral.state_changed.connect(self.state_changed.emit)
        self.axis_heading.state_changed.connect(self.state_changed.emit)
        self.bbox_tl.state_changed.connect(self.state_changed.emit)
        self.bbox_tr.state_changed.connect(self.state_changed.emit)
        self.bbox_bl.state_changed.connect(self.state_changed.emit)
        self.bbox_br.state_changed.connect(self.state_changed.emit)

        self.origin.selected_signal.connect(self._on_child_handle_selected)
        self.axis_lateral.selected_signal.connect(self._on_child_handle_selected)
        self.axis_heading.selected_signal.connect(self._on_child_handle_selected)
        self.bbox_tl.selected_signal.connect(self._on_child_handle_selected)
        self.bbox_tr.selected_signal.connect(self._on_child_handle_selected)
        self.bbox_bl.selected_signal.connect(self._on_child_handle_selected)
        self.bbox_br.selected_signal.connect(self._on_child_handle_selected)

        self.update_axis_positions()
        self.update_bbox_positions()

    def toggle_lock(self):
        self.is_locked = not self.is_locked
        self.btn_lock.text = "🔒" if self.is_locked else "🔓"
        self.btn_lock.bg_color = QColor(190, 140, 0, 180) if self.is_locked else QColor(60, 60, 60, 180)
        self.btn_lock.update()
        self.state_changed.emit()

    def _on_delete_clicked(self):
        if self.parent_widget:
            self.parent_widget.remove_coordinate_system(self.index)

    def _on_child_handle_selected(self):
        self.setSelected(True)
        self.selected_signal.emit(self.index)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange and value == True:
            self.selected_signal.emit(self.index)
        return super().itemChange(change, value)

    def hoverEnterEvent(self, event):
        if not self.axes_visible and not self.is_locked:
            self.setCursor(Qt.SizeAllCursor)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        self.setSelected(True)
        self.selected_signal.emit(self.index)
        
        if event.button() == Qt.LeftButton and not self.is_locked:
            self._drag_start_scene = event.scenePos()
            self._drag_start_pos = self.pos()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and not self.is_locked:
            delta = event.scenePos() - self._drag_start_scene
            self.handle_origin_move(delta, self._drag_start_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.state_changed.emit()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def set_axes_visible(self, visible: bool):
        self.prepareGeometryChange()
        
        if visible and not self.axes_visible:
            bbox_center_scene = self.mapToScene(QPointF(self._bbox_cx, self._bbox_cy))
            self.setPos(bbox_center_scene)
            self._bbox_cx = 0.0
            self._bbox_cy = 0.0
            
        elif not visible and self.axes_visible:
            scene_center = self.mapToScene(QPointF(self._bbox_cx, self._bbox_cy))
            self.setPos(scene_center)
            self._bbox_cx = 0.0
            self._bbox_cy = 0.0
            
        self.axes_visible = visible
        self.axis_lateral.setVisible(visible)
        self.axis_heading.setVisible(visible)
        self.origin.setVisible(visible) 
        
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
        self.label_item.setPos(self.bbox_tl.pos())

    def get_bbox_rect(self):
        return QRectF(self._bbox_cx - self._bbox_w / 2.0, 
                      self._bbox_cy - self._bbox_h / 2.0, 
                      self._bbox_w, self._bbox_h)

    def boundingRect(self):
        bbox = self.get_bbox_rect()
        if not self.axes_visible:
            return bbox.adjusted(-15, -15, 15, 15)
        axes_rect = QRectF(self.origin.pos(), self.axis_lateral.pos()).united(QRectF(self.origin.pos(), self.axis_heading.pos()))
        return bbox.united(axes_rect).adjusted(-35, -20, 20, 35)

    def shape(self):
        path = QPainterPath()
        if self.axes_visible:
            path.moveTo(self.origin.pos())
            path.lineTo(self.axis_lateral.pos())
            path.moveTo(self.origin.pos())
            path.lineTo(self.axis_heading.pos())
            
            stroker = QPainterPathStroker()
            stroker.setWidth(16)
            stroker.setCapStyle(Qt.RoundCap)
            total_shape = stroker.createStroke(path)
            total_shape.addRect(self.get_bbox_rect())
        else:
            path.addRect(self.get_bbox_rect())
            total_shape = path
            
        total_shape.addPath(self.bbox_tl.mapToParent(self.bbox_tl.shape()))
        total_shape.addPath(self.bbox_tr.mapToParent(self.bbox_tr.shape()))
        total_shape.addPath(self.bbox_bl.mapToParent(self.bbox_bl.shape()))
        total_shape.addPath(self.bbox_br.mapToParent(self.bbox_br.shape()))
        
        # Register buttons bounds into item shape
        total_shape.addPath(self.btn_delete.mapToParent(self.btn_delete.shape()))
        total_shape.addPath(self.btn_lock.mapToParent(self.btn_lock.shape()))
        
        if self.axes_visible:
            total_shape.addPath(self.origin.mapToParent(self.origin.shape()))
            total_shape.addPath(self.axis_lateral.mapToParent(self.axis_lateral.shape()))
            total_shape.addPath(self.axis_heading.mapToParent(self.axis_heading.shape()))
            
        return total_shape

    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Adjust styling slightly if it's locked to visually represent lock state
        if self.isSelected():
            color = QColor(130, 130, 130, 150) if self.is_locked else self.color_bbox_selected
            bbox_pen = QPen(color, 2.5, Qt.DashLine)
            bbox_pen.setCosmetic(True)
            painter.setPen(bbox_pen)
            if not self.axes_visible:
                painter.setBrush(QBrush(QColor(color.red(), color.green(), color.blue(), 15)))
        else:
            color = QColor(150, 150, 150, 100) if self.is_locked else self.color_bbox
            bbox_pen = QPen(color, 2.0, Qt.DashLine)
            bbox_pen.setCosmetic(True)
            painter.setPen(bbox_pen)
            painter.setBrush(Qt.NoBrush)
            
        painter.drawRect(self.get_bbox_rect())

        if self.axes_visible:
            lat_pen = QPen(QColor(self.color_lateral.red(), self.color_lateral.green(), self.color_lateral.blue(), 230), 3.0)
            lat_pen.setCosmetic(True)
            painter.setPen(lat_pen)
            painter.drawLine(self.origin.pos(), self.axis_lateral.pos())
            
            head_pen = QPen(QColor(self.color_heading.red(), self.color_heading.green(), self.color_heading.blue(), 230), 3.0)
            head_pen.setCosmetic(True)
            painter.setPen(head_pen)
            painter.drawLine(self.origin.pos(), self.axis_heading.pos())

    def handle_origin_move(self, delta: QPointF, drag_start_parent_pos: QPointF):
        scene = self.scene()
        if not scene or self.is_locked:
            return
            
        self.prepareGeometryChange()
        
        target_scene_pos = drag_start_parent_pos + delta
        scene_rect = scene.sceneRect()
        
        hw, hh = self._bbox_w / 2.0, self._bbox_h / 2.0
        local_left = self._bbox_cx - hw
        local_right = self._bbox_cx + hw
        local_top = self._bbox_cy - hh
        local_bottom = self._bbox_cy + hh
        
        min_x = scene_rect.left() - local_left
        max_x = scene_rect.right() - local_right
        min_y = scene_rect.top() - local_top
        max_y = scene_rect.bottom() - local_bottom
        
        clamped_x = max(min_x, min(target_scene_pos.x(), max_x))
        clamped_y = max(min_y, min(target_scene_pos.y(), max_y))
        
        self.setPos(QPointF(clamped_x, clamped_y))
        self.update()

    def handle_axis_drag(self, node, local_mouse_pos):
        if self.is_locked:
            return
        self.prepareGeometryChange()
        dx, dy = local_mouse_pos.x(), local_mouse_pos.y()
        if node == self.axis_lateral:
            self._current_angle = math.atan2(dy, dx)
        elif node == self.axis_heading:
            self._current_angle = math.atan2(dy, dx) + (math.pi / 2.0)
        self.update_axis_positions()
        self.update()

    def handle_bbox_resize(self, node, local_mouse_pos):
        if self.is_locked:
            return
        self.prepareGeometryChange()
        self._resize_asymmetric(node, local_mouse_pos)
        self.update_bbox_positions()
        self.update()

    def _resize_asymmetric(self, node, local_mouse_pos):
        scene = self.scene()
        if not scene:
            return

        mx, my = local_mouse_pos.x(), local_mouse_pos.y()
        hw, hh = self._bbox_w / 2.0, self._bbox_h / 2.0
        x1, x2 = self._bbox_cx - hw, self._bbox_cx + hw  
        y1, y2 = self._bbox_cy - hh, self._bbox_cy + hh  

        if self.axes_visible:
            if "br" in node.corner_id:
                mx, my = max(0.0, mx), max(0.0, my)
            elif "tl" in node.corner_id:
                mx, my = min(0.0, mx), min(0.0, my)
            elif "tr" in node.corner_id:
                mx, my = max(0.0, mx), min(0.0, my)
            elif "bl" in node.corner_id:
                mx, my = min(0.0, mx), max(0.0, my)
        else:
            if "r" in node.corner_id:
                mx = max(x1 + 20.0, mx)
            if "l" in node.corner_id:
                mx = min(x2 - 20.0, mx)
            if "b" in node.corner_id:
                my = max(y1 + 20.0, my)
            if "t" in node.corner_id:
                my = min(y2 - 20.0, my)

        if "br" in node.corner_id:
            x2, y2 = mx, my
        elif "tl" in node.corner_id:
            x1, y1 = mx, my
        elif "tr" in node.corner_id:
            x2, y1 = mx, my
        elif "bl" in node.corner_id:
            x1, y2 = mx, my

        tentative_tl = self.mapToScene(QPointF(x1, y1))
        tentative_br = self.mapToScene(QPointF(x2, y2))
        
        scene_rect = scene.sceneRect()
        clamped_tl_x = max(scene_rect.left(), min(tentative_tl.x(), scene_rect.right()))
        clamped_tl_y = max(scene_rect.top(), min(tentative_tl.y(), scene_rect.bottom()))
        clamped_br_x = max(scene_rect.left(), min(tentative_br.x(), scene_rect.right()))
        clamped_br_y = max(scene_rect.top(), min(tentative_br.y(), scene_rect.bottom()))

        local_tl = self.mapFromScene(QPointF(clamped_tl_x, clamped_tl_y))
        local_br = self.mapFromScene(QPointF(clamped_br_x, clamped_br_y))

        self._bbox_w = max(20.0, local_br.x() - local_tl.x())
        self._bbox_h = max(20.0, local_br.y() - local_tl.y())
        self._bbox_cx = local_tl.x() + self._bbox_w / 2.0
        self._bbox_cy = local_tl.y() + self._bbox_h / 2.0

    def get_state(self) -> dict:
        bbox_tl_scene_pos = self.mapToScene(self.bbox_tl.pos())

        x = int(round(bbox_tl_scene_pos.x()))
        y = int(round(bbox_tl_scene_pos.y()))
        w = int(round(self._bbox_w))
        h = int(round(self._bbox_h))
        
        centroid_x = int(round(-self.bbox_tl.x()))
        centroid_y = int(round(-self.bbox_tl.y()))
        
        return {
            "is_locked": self.is_locked,
            "axes_visible": self.axes_visible,
            "bbox_rect": [x, y, w, h],
            "centroid": [centroid_x, centroid_y],
            "axes": [
                [(self.axis_heading.x() - self.origin.x()) / self._len_heading, (self.axis_lateral.x() - self.origin.x()) / self._len_lateral],
                [(self.axis_heading.y() - self.origin.y()) / self._len_heading, (self.axis_lateral.y() - self.origin.y()) / self._len_lateral]
            ]
        }

    def set_state(self, data: dict):
        self.prepareGeometryChange()
        x, y, w, h = data["bbox_rect"]
        offset_x, offset_y = data["centroid"]
        
        self._bbox_w = float(w)
        self._bbox_h = float(h)
        self._bbox_cx = (self._bbox_w / 2.0) - float(offset_x)
        self._bbox_cy = (self._bbox_h / 2.0) - float(offset_y)
        
        self.setPos(QPointF(float(x + offset_x), float(y + offset_y)))
        
        axes = data["axes"]
        self._current_angle = math.atan2(axes[1][1], axes[0][1])

        self.set_axes_visible(data["axes_visible"])
        
        if "is_locked" in data and data["is_locked"] != self.is_locked:
            self.toggle_lock()
            
        self.update_axis_positions()
        self.update_bbox_positions()
        self.update()


class MultiCoordViewer(QGraphicsView):
    state_changed = Signal()
    selection_changed = Signal(int)
    systems_reindexed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setBackgroundBrush(QBrush(QColor(40, 40, 40)))
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        self.coordinate_systems = [] 
        self.bg_pixmap_item = None
        self._global_axes_visible = False
        self.selected_index = -1

    def set_selected_index(self, index: int):
        if self.selected_index == index and index != -1:
            return
            
        self.selected_index = index
        for sys_item in self.coordinate_systems:
            is_selected = (sys_item.index == index)
            sys_item.setSelected(is_selected)
            
            if is_selected:
                sys_item.setZValue(1.0)  
            else:
                sys_item.setZValue(0.0) 
                
        self.selection_changed.emit(self.selected_index)

    def set_axes_visible(self, visible: bool):
        for sys_item in self.coordinate_systems:
            sys_item.set_axes_visible(visible)
        self._global_axes_visible = visible
        self.state_changed.emit()

    def wheelEvent(self, event):
        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor
        self.scale(zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor, 
                   zoom_in_factor if event.angleDelta().y() > 0 else zoom_out_factor)
        event.accept()

    def mousePressEvent(self, event: QMouseEvent):
        item = self.itemAt(event.pos())
        if item is None or item == self.bg_pixmap_item:
            self.set_selected_index(-1)

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.bg_pixmap_item:
            self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)

    def set_background_image(self, image: NDArray):
        # Fallback to standard check if implementation relies on exterior script logic
        try:
            from qt_widgets import NDarray_to_QPixmap
            pixmap = NDarray_to_QPixmap(image)
        except ImportError:
            return
            
        if self.bg_pixmap_item in self.scene.items(): 
            self.scene.removeItem(self.bg_pixmap_item)
        self.bg_pixmap_item = self.scene.addPixmap(pixmap)
        self.bg_pixmap_item.setZValue(-100)
        image_rect = QRectF(pixmap.rect())
        self.setSceneRect(QRectF(pixmap.rect()))
        self.scene.setSceneRect(image_rect)
        
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)
        self.state_changed.emit()

    def add_coordinate_system(self, scene_pos: QPointF):
        if self.bg_pixmap_item:
            s_rect = self.sceneRect()
            scene_pos.setX(max(s_rect.left(), min(scene_pos.x(), s_rect.right())))
            scene_pos.setY(max(s_rect.top(), min(scene_pos.y(), s_rect.bottom())))

        index = len(self.coordinate_systems)
        coord_sys = InteractiveCoordinateSystem(index, scene_pos, self)
        coord_sys.state_changed.connect(self.state_changed)
        coord_sys.selected_signal.connect(self.set_selected_index)
        coord_sys.set_axes_visible(self._global_axes_visible)
        
        self.scene.addItem(coord_sys)
        self.coordinate_systems.append(coord_sys)
        
        self.set_selected_index(index)
        self.state_changed.emit()

    def remove_coordinate_system(self, index: int):
        if 0 <= index < len(self.coordinate_systems):
            item = self.coordinate_systems.pop(index)
            self.scene.removeItem(item)
            self.reindex_systems()
            
            new_selection = len(self.coordinate_systems) - 1 if self.coordinate_systems else -1
            self.set_selected_index(new_selection)

    def clear_coordinate_systems(self):
        for sys_item in self.coordinate_systems:
            self.scene.removeItem(sys_item)
        self.coordinate_systems.clear()
        self.set_selected_index(-1)
        self.state_changed.emit()

    def reindex_systems(self):
        index_mapping = {}
        for idx, sys_item in enumerate(self.coordinate_systems):
            old_idx = sys_item.index
            index_mapping[old_idx] = idx
            
            sys_item.index = idx
            sys_item.label_item.text = str(idx) 
            sys_item.update() 
            
        self.scene.update()
        self.state_changed.emit()
        self.systems_reindexed.emit(index_mapping)

    def get_state(self) -> dict:
        data = {'n_animals': len(self.coordinate_systems), 'identities': {}}
        for idx, sys_item in enumerate(self.coordinate_systems):
            data['identities'][idx] = sys_item.get_state()
        return data
    
    def set_state(self, data: dict):
        self.clear_coordinate_systems()
        identities = data.get("identities", {})

        for str_idx in sorted(identities.keys(), key=int):
            idx = int(str_idx)
            item_data = identities[str_idx]
            
            x, y, _, _ = item_data["bbox_rect"]
            offset_x, offset_y = item_data["centroid"]
            initial_pos = QPointF(x + offset_x, y + offset_y)
            
            coord_sys = InteractiveCoordinateSystem(idx, initial_pos, self)
            coord_sys.state_changed.connect(self.state_changed)
            coord_sys.selected_signal.connect(self.set_selected_index)
            coord_sys.set_axes_visible(self._global_axes_visible)
            coord_sys.set_state(item_data)
            
            self.scene.addItem(coord_sys)
            self.coordinate_systems.append(coord_sys)
            
        self.scene.update()