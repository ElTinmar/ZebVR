from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout,
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

    def __init__(
            self,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.layout = QVBoxLayout(self)
        self.setWindowTitle('Queue Monitor')

    def add_progress_bar(self, queue_widget: QueueWidget):
        self.layout.addWidget(queue_widget)