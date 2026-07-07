import sys
from qtpy.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTreeView, 
    QProgressBar, QLabel, QHeaderView, QScrollArea, QSizePolicy, QScroller
)
from qtpy.QtGui import QStandardItemModel, QStandardItem
from qtpy.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve

TREE_WIDTH = 512
SPACING = 20

class ContentAutoSizedTreeView(QTreeView):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.setFixedWidth(TREE_WIDTH)

    def sizeHint(self):
        hint = super().sizeHint()
        hint.setHeight(self.viewportSizeHint().height())
        return hint

class ProtocolDisplay(QWidget):

    def __init__(self, recording_duration: float = 100):
        super().__init__()
        self.recording_duration = recording_duration
        self.current_time = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        layout.addWidget(QLabel("<b>Protocol:</b>"))
        
        # 1. Main Horizontal Scroll Container
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        hbar = self.scroll_area.horizontalScrollBar()
        hbar.setSingleStep(2)
        
        # Enable smooth kinematic touch/mouse-drag scrolling natively (optional gesture control)
        QScroller.grabGesture(self.scroll_area.viewport(), QScroller.LeftMouseButtonGesture)
        
        self.history_container = QWidget()
        self.history_layout = QHBoxLayout(self.history_container)
        self.history_layout.setContentsMargins(10, 10, 10, 10)
        self.history_layout.setSpacing(SPACING) # Clear gaps to clearly separate history units
        
        self.scroll_area.setWidget(self.history_container)
        layout.addWidget(self.scroll_area)
        
        layout.addWidget(QLabel("<b>Progress:</b>"))
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, int(self.recording_duration))
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat(f"0 / {int(self.recording_duration)}s")
        layout.addWidget(self.progress_bar)
        
        self.setWindowTitle("Protocol Viewer")
        self.resize(TREE_WIDTH+2*SPACING, 700) 

    def create_new_tree_view(self, data: dict) -> QTreeView:
        tree_view = ContentAutoSizedTreeView()
        
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(["Parameter", "Value"])
        tree_view.setModel(model)
        
        root_node = model.invisibleRootItem()
        self._recurse_tree(data, root_node, model)
        tree_view.expandAll()
        
        header = tree_view.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        
        tree_view.updateGeometry()
        return tree_view

    def _recurse_tree(self, data, parent_item, model):
        if isinstance(data, dict):
            for key, value in data.items():
                key_item = QStandardItem(str(key))
                if isinstance(value, (dict, list)):
                    parent_item.appendRow([key_item, QStandardItem("")])
                    self._recurse_tree(value, key_item, model)
                else:
                    value_item = QStandardItem(str(value))
                    parent_item.appendRow([key_item, value_item])
                    
        elif isinstance(data, list):
            for index, value in enumerate(data):
                key_item = QStandardItem(f"[{index}]")
                if isinstance(value, (dict, list)):
                    parent_item.appendRow([key_item, QStandardItem("")])
                    self._recurse_tree(value, key_item, model)
                else:
                    value_item = QStandardItem(str(value))
                    parent_item.appendRow([key_item, value_item])

    def set_stim_data(self, stim_data: dict):
        if self.history_layout.count() == 0:
            self.start_timer()

        new_tree = self.create_new_tree_view(stim_data)
        self.history_layout.addWidget(new_tree)
        
        # Smoothly glide view context to the right
        QTimer.singleShot(100, self.smooth_scroll_to_end)

    def smooth_scroll_to_end(self):
        """Animates the scrollbar slider cleanly using an easing curve to maintain context."""
        hbar = self.scroll_area.horizontalScrollBar()
        start_value = hbar.value()
        end_value = hbar.maximum()
        
        # Set up a target property animation tracking the slider value
        self.anim = QPropertyAnimation(hbar, b"value")
        self.anim.setDuration(600) # Duration in milliseconds
        self.anim.setStartValue(start_value)
        self.anim.setEndValue(end_value)
        self.anim.setEasingCurve(QEasingCurve.OutCubic) # Clean deceleration curve
        self.anim.start()

    def start_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(1000)

    def update_progress(self):
        if self.current_time < self.recording_duration:
            self.current_time += 1.0
            progress_text = f"{int(self.current_time)} / {int(self.recording_duration)}s"
            self.progress_bar.setFormat(progress_text)
            self.progress_bar.setValue(int(self.current_time))
        else:
            self.progress_bar.setFormat(f"{int(self.recording_duration)}s / {int(self.recording_duration)}s (Complete)")
            self.timer.stop()  


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = ProtocolDisplay(recording_duration=30)
    widget.show()

    data_1 = {"project": "Dashboard Run A", "version": 1.0}
    data_2 = {"project": "Dashboard Run B", "metadata": {"author": "Alice"}}
    data_3 = {"project": "Dashboard Run C", "status": "Finished!"}

    widget.set_stim_data(data_1)
    
    QTimer.singleShot(2000, lambda: widget.set_stim_data(data_2))
    QTimer.singleShot(4000, lambda: widget.set_stim_data(data_3))

    sys.exit(app.exec_())