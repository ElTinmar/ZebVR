from PyQt5.QtWidgets import (
    QWidget, 
    QGridLayout,
    QHBoxLayout,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QLabel
)
from PyQt5.QtCore import Qt
from typing import Optional

#TODO add dropped frames and fps

class QueueWidget(QWidget):

    def __init__(
            self,
            name: str,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)

        self.name = name
        self.declare_components()
        self.layout_components()

    def declare_components(self) -> None:
        self.name_label = QLabel(self.name)
        self.progress_bar = QProgressBar()

    def layout_components(self) -> None:
        layout = QHBoxLayout(self)
        layout.addWidget(self.name_label)
        layout.addWidget(self.progress_bar)

    def set_state(self, count: Optional[int], max: Optional[int]) -> None:
        if count is not None:
            self.progress_bar.setValue(count)
        if max is not None:
            self.progress_bar.setMaximum(max)
        self.update()

class QueueMonitorWidget(QWidget):

    MAX_ROWS = 10
    FIXED_HEIGHT = 480

    def __init__(
            self,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.widget_count = 0

        self.layout = QVBoxLayout(self)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFixedHeight(self.FIXED_HEIGHT)
        self.layout.addWidget(self.scroll_area)

        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setSpacing(0)
        self.grid.setContentsMargins(0, 0, 0, 0) 
        self.scroll_area.setWidget(self.container) 
        
        self.setWindowTitle('Queue Monitor')

    def add_progress_bar(self, queue_widget: QueueWidget):
        row = self.widget_count % self.MAX_ROWS
        col = self.widget_count // self.MAX_ROWS
        self.grid.addWidget(queue_widget, row, col)
        self.widget_count += 1