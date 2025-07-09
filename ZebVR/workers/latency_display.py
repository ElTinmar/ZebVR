import sys
import queue
import random
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QTextEdit, QVBoxLayout, QHBoxLayout
)
from PyQt5.QtCore import QTimer, pyqtSignal, QObject
import pyqtgraph as pg

LATENCY_THRESHOLD_MS = 14.0
MAX_HISTORY = 30
MAX_HIST_SAMPLES = 1000

class LatencyCollector(QObject):
    new_latency = pyqtSignal(int, int, float)

    def report_latency(self, frame, fish_id, latency):
        self.new_latency.emit(frame, fish_id, latency)


class LatencyDisplay(QWidget):
    def __init__(self, history_size=MAX_HISTORY):
        super().__init__()
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.history_size = history_size
        self.history = []
        self.q = queue.Queue()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Recent Latency:"))
        layout.addWidget(self.text)
        self.setLayout(layout)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(1/30) 

    def receive_latency(self, frame, fish_id, latency):
        msg = f"frame {frame}, fish {fish_id}: latency {latency:.3f}"
        self.q.put((latency, msg))

    def update_display(self):
        while not self.q.empty():
            latency, msg = self.q.get_nowait()
            if len(self.history) >= self.history_size:
                self.history.pop(0)
            if latency > LATENCY_THRESHOLD_MS:
                msg = f'<span style="color:red">{msg}</span>'
            self.history.append(msg)

        self.text.setHtml("<br>".join(self.history))


class LatencyHistogram(QWidget):
    def __init__(self, max_samples=MAX_HIST_SAMPLES):
        super().__init__()
        self.latencies = []
        self.max_samples = max_samples
        self.q = queue.Queue()

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

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_histogram)
        self.timer.start(200)  # Update every 200 ms

    def receive_latency(self, frame, fish_id, latency):
        self.q.put(latency)

    def update_histogram(self):
        while not self.q.empty():
            val = self.q.get_nowait()
            self.latencies.append(val)
            if len(self.latencies) > self.max_samples:
                self.latencies.pop(0)

        if self.latencies:
            counts, bins = np.histogram(self.latencies, bins='auto')
            self.hist_plot.setData(bins, counts, stepMode=True, fillLevel=0, brush=(150, 150, 255, 150))


class LatencyMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Latency Monitor")
        self.resize(800, 400)

        self.collector = LatencyCollector()
        self.display = LatencyDisplay()
        self.histogram = LatencyHistogram()

        # Connect both widgets to the same signal
        self.collector.new_latency.connect(self.display.receive_latency)
        self.collector.new_latency.connect(self.histogram.receive_latency)

        layout = QHBoxLayout()
        layout.addWidget(self.display, 2)
        layout.addWidget(self.histogram, 3)
        self.setLayout(layout)

        # Simulate latency input
        self.frame_counter = 0
        self.sim_timer = QTimer()
        self.sim_timer.timeout.connect(self.simulate_latency)
        self.sim_timer.start(1000/100)  # 100 Hz input

    def simulate_latency(self):
        latency = random.uniform(10, 13)
        if random.random() < 0.1:
            latency += random.uniform(3, 6)  # occasional spike
        self.collector.report_latency(self.frame_counter, 0, latency)
        self.frame_counter += 1


if __name__ == "__main__":
    app = QApplication(sys.argv)
    monitor = LatencyMonitor()
    monitor.show()
    sys.exit(app.exec_())
