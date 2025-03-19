from PyQt5.QtWidgets import (
    QWidget, 
    QGridLayout,
    QHBoxLayout,
    QProgressBar,
    QLabel
)
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

    def declare_components(self):
        self.name_label = QLabel(self.name)
        self.progress_bar = QProgressBar()

    def layout_components(self):
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

    def __init__(
            self,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.widget_count = 0
        self.layout = QGridLayout(self)
        self.setWindowTitle('Queue Monitor')

    def add_progress_bar(self, queue_widget: QueueWidget):
        row = self.widget_count % self.MAX_ROWS
        col = self.widget_count // self.MAX_ROWS
        self.layout.addWidget(queue_widget, row, col)
        self.widget_count += 1