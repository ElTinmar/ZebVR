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
        self.setFlags(QGraphicsItem.ItemSendsGeometryChanges)
        
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
        scene = self.scene()

        if parent and scene and (event.buttons() & Qt.LeftButton):
            delta = event.scenePos() - self._drag_start_scene
            parent.handle_origin_move(delta, self._drag_start_parent_pos)
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


class InteractiveCoordinateSystem(QGraphicsObject):
    state_changed = Signal()
    selected_signal = Signal(int)

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
        self.color_bbox_selected = QColor(0, 255, 127, 220)  

        # Child handles initialization
        self.origin = OriginHandle(self.color_origin, parent=self)
        self.origin.setPos(0, 0)

        self.axis_lateral = AxisHandle(self.color_lateral, parent=self)
        self.axis_heading = AxisHandle(self.color_heading, parent=self)
        
        self.bbox_tl = BBoxCornerHandle(self.color_bbox, "tl", parent=self)
        self.bbox_tr = BBoxCornerHandle(self.color_bbox, "tr", parent=self)
        self.bbox_bl = BBoxCornerHandle(self.color_bbox, "bl", parent=self)
        self.bbox_br = BBoxCornerHandle(self.color_bbox, "br", parent=self)

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

    def _on_child_handle_selected(self):
        self.setSelected(True)
        self.selected_signal.emit(self.index)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange and value == True:
            self.selected_signal.emit(self.index)
        return super().itemChange(change, value)

    def mousePressEvent(self, event):
        self.setSelected(True)
        self.selected_signal.emit(self.index)
        super().mousePressEvent(event)

    def set_axes_visible(self, visible: bool):
        self.prepareGeometryChange()
        self.axes_visible = visible
        self.axis_lateral.setVisible(visible)
        self.axis_heading.setVisible(visible)

        if not self.axes_visible:
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
        
        if self.isSelected():
            painter.setPen(QPen(self.color_bbox_selected, 2.5, Qt.DashLine))
        else:
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

    def handle_origin_move(self, delta: QPointF, drag_start_parent_pos: QPointF):
        scene = self.scene()
        if not scene:
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
        self.prepareGeometryChange()
        dx, dy = local_mouse_pos.x(), local_mouse_pos.y()
        if node == self.axis_lateral:
            self._current_angle = math.atan2(dy, dx)
        elif node == self.axis_heading:
            self._current_angle = math.atan2(dy, dx) + (math.pi / 2.0)
        self.update_axis_positions()
        self.update()

    def handle_bbox_resize(self, node, local_mouse_pos):
        self.prepareGeometryChange()
        
        if self.axes_visible:
            self._resize_asymmetric(node, local_mouse_pos)
        else:
            self._resize_symmetric(local_mouse_pos)
    
        self.update_bbox_positions()
        self.update()

    def _resize_asymmetric(self, node, local_mouse_pos):
        scene = self.scene()
        if not scene:
            return

        # 1. Enforce that the corner cannot cross over the origin (0, 0)
        # This restores your core quadrant constraint.
        mx, my = local_mouse_pos.x(), local_mouse_pos.y()
        if "br" in node.corner_id:
            mx, my = max(0.0, mx), max(0.0, my)
        elif "tl" in node.corner_id:
            mx, my = min(0.0, mx), min(0.0, my)
        elif "tr" in node.corner_id:
            mx, my = max(0.0, mx), min(0.0, my)
        elif "bl" in node.corner_id:
            mx, my = min(0.0, mx), max(0.0, my)

        # 2. Extract current local boundaries
        hw, hh = self._bbox_w / 2.0, self._bbox_h / 2.0
        x1, x2 = self._bbox_cx - hw, self._bbox_cx + hw  
        y1, y2 = self._bbox_cy - hh, self._bbox_cy + hh  

        # 3. Update the target corner using our origin-constrained coordinates
        if "br" in node.corner_id:
            x2, y2 = mx, my
        elif "tl" in node.corner_id:
            x1, y1 = mx, my
        elif "tr" in node.corner_id:
            x2, y1 = mx, my
        elif "bl" in node.corner_id:
            x1, y2 = mx, my

        # 4. Enforce scene rect boundaries (ensure box doesn't leave the image)
        tentative_tl = self.mapToScene(QPointF(x1, y1))
        tentative_br = self.mapToScene(QPointF(x2, y2))
        
        scene_rect = scene.sceneRect()
        clamped_tl_x = max(scene_rect.left(), min(tentative_tl.x(), scene_rect.right()))
        clamped_tl_y = max(scene_rect.top(), min(tentative_tl.y(), scene_rect.bottom()))
        clamped_br_x = max(scene_rect.left(), min(tentative_br.x(), scene_rect.right()))
        clamped_br_y = max(scene_rect.top(), min(tentative_br.y(), scene_rect.bottom()))

        # 5. Convert back to local variables to safely finalize box geometry
        local_tl = self.mapFromScene(QPointF(clamped_tl_x, clamped_tl_y))
        local_br = self.mapFromScene(QPointF(clamped_br_x, clamped_br_y))

        self._bbox_w = max(20.0, local_br.x() - local_tl.x())
        self._bbox_h = max(20.0, local_br.y() - local_tl.y())
        self._bbox_cx = local_tl.x() + self._bbox_w / 2.0
        self._bbox_cy = local_tl.y() + self._bbox_h / 2.0

    def _resize_symmetric(self, local_mouse_pos):
        scene = self.scene()
        if not scene:
            return

        scene_rect = scene.sceneRect()
        parent_scene_pos = self.scenePos()

        max_hw = min(parent_scene_pos.x() - scene_rect.left(), scene_rect.right() - parent_scene_pos.x())
        max_hh = min(parent_scene_pos.y() - scene_rect.top(), scene_rect.bottom() - parent_scene_pos.y())

        target_hw = min(abs(local_mouse_pos.x()), max_hw)
        target_hh = min(abs(local_mouse_pos.y()), max_hh)

        self._bbox_w = max(20.0, target_hw * 2.0)
        self._bbox_h = max(20.0, target_hh * 2.0)
        self._bbox_cx = 0.0
        self._bbox_cy = 0.0

    def get_state(self) -> dict:
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
    
    def set_state(self, data: dict):
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
    state_changed = Signal()
    selection_changed = Signal(int)

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
            is_target = (sys_item.index == index)
            sys_item.setSelected(is_target)
                
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
        pixmap = NDarray_to_QPixmap(image)
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
        for idx, sys_item in enumerate(self.coordinate_systems):
            sys_item.index = idx
            sys_item.update() 
        self.scene.update()
        self.state_changed.emit()

    def get_state(self) -> dict:
        data = {}
        data['n_animals'] = len(self.coordinate_systems)
        data['identities'] = {}
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