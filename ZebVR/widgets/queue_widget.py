from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout,
    QProgressBar
)

# add dropped frames

class QueueWidget(QWidget):

    def __init__(
            self,
            queue_size: int,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)

        self.queue_size = queue_size
        self.declare_components()
        self.layout_components()

    def declare_components(self):
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(self.queue_size)

    def layout_components(self):
        layout = QVBoxLayout(self)
        layout.addWidget(self.progress_bar)

    def set_state(self, count: int) -> None:
        self.progress_bar.setValue(count)
        self.update()

class QueueMonitorWidget(QWidget):

    def __init__(
            self,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.layout = QVBoxLayout(self)
        self.queue_widgets = []

    def add_progress_bar(self, queue_widget: QueueWidget):
        self.queue_widgets.append(queue_widget)
        self.layout.addWidget(queue_widget)