import sys
import queue
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QTextEdit, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import QTimer
import pyqtgraph as pg
from dagline import WorkerNode
from typing import Dict, Optional
from collections import deque

LATENCY_THRESHOLD_MS = 20.0
MAX_HISTORY = 30
MAX_HIST_SAMPLES = 500

class LatencyText(QWidget):
    def __init__(
            self, 
            history_size: int = MAX_HISTORY
        ):
        super().__init__()
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.data = deque(maxlen = history_size)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Recent Latency:"))
        layout.addWidget(self.text)
        self.setLayout(layout)

    def receive_latency(self, frame, fish_id, latency):
        msg = f"frame {frame}, fish {fish_id}: latency {latency:.3f}"
        self.data.append((latency, msg))

    @staticmethod
    def highlight_msg(msg: str, flag: bool):
        out = msg
        if flag:
            out = f'<span style="color:red">{msg}</span>'
        return out 

    def update_display(self):
        text = [self.highlight_msg(msg, latency > LATENCY_THRESHOLD_MS) for latency, msg in self.data]
        self.text.setHtml("<br>".join(text))

class LatencyHistogram(QWidget):
    
    def __init__(
            self, 
            num_samples: int = MAX_HIST_SAMPLES
        ):

        super().__init__()

        self.data = deque(maxlen = num_samples)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.enableAutoRange(axis='x', enable=True)
        self.plot_widget.enableAutoRange(axis='y', enable=True)
        self.plot_widget.setLabel('bottom', 'Latency (ms)')
        self.plot_widget.setLabel('left', 'Count')
        self.hist_plot = self.plot_widget.plot(stepMode=True, fillLevel=0, brush=(150, 150, 255, 150))

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Latency Histogram:"))
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

    def receive_latency(self, latency):
        self.data.append(latency)

    def update_histogram(self):
        if self.data:
            counts, bins = np.histogram(self.data, bins='auto')
            self.hist_plot.setData(bins, counts)

class LatencyWidget(QWidget):

    def __init__(
            self,
            refresh_frequency,
        ):

        super().__init__()

        self.text_display = LatencyText()
        self.histogram = LatencyHistogram()

        layout = QHBoxLayout()
        layout.addWidget(self.text_display, 2)
        layout.addWidget(self.histogram, 3)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(1000/refresh_frequency) 

    def add_data(self, frame, fish_id, latency):
        self.text_display.receive_latency(frame, fish_id, latency)
        self.histogram.receive_latency(latency)

    def update_display(self):
        self.text_display.update_display()
        self.histogram.update_histogram()

class LatencyDisplay(WorkerNode):

    def __init__(
            self, 
            refresh_frequency: int = 30,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.refresh_frequency = refresh_frequency

    def initialize(self) -> None:

        super().initialize()

        self.app = QApplication([])
        self.window = LatencyWidget(self.refresh_frequency)
        self.window.show()

    def process_data(self, data):
             
        self.app.processEvents()
        self.app.sendPostedEvents()

        if data is not None:
            self.window.add_data(
                    data['frame'],
                    data['fish_id'],
                    data['latency']
                )

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        pass
        

