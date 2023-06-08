from typing import Any
from core.abstractclasses import DataPlotter
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class DataPlot(DataPlotter):
    def __init__(self) -> None:
        super().__init__()
        
        self.fig, self.ax = plt.subplots()
        self.xdata, self.ydata = [], []
        self.line, = self.ax.plot([], [], 'ro')
        self.ani = FuncAnimation(self.fig, self.plot, self.format_data,
                    init_func=self.init_plot, blit=True)
        plt.show()

    def init_plot(self):
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(-1, 1)
        return self.line,

    def format_data(self, data: dict):
        """
        Receive data as a dict
        """
        yield data['x'],data['y']

    def plot(self, data) -> None:
        """
        Input dictionary with keys legend, x, y
        """
        x, y = data
        self.xdata.append(x)
        self.ydata.append(y)
        xmin, xmax = self.ax.get_xlim()

        if x >= xmax:
            self.ax.set_xlim(xmin, 2*xmax)
            self.ax.figure.canvas.draw()
        self.line.set_data(self.xdata, self.ydata)

        return self.line,        