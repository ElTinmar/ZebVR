from typing import Any
from core.abstractclasses import DataPlotter
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from multiprocessing import Process, Array

class DataPlot(DataPlotter):
    def __init__(self) -> None:
        super().__init__()
        
        self.fig, self.ax = plt.subplots()
        self.xdata = Array('d',100) 
        self.ydata = Array('d',100)
        self.line, = self.ax.plot(self.xdata, self.ydata, 'ro')
        self.proc = Process(target=self.animate)
        
    def start(self):
        self.proc.start()

    def stop(self):
        self.proc.join()

    def animate(self):
        self.ani = FuncAnimation(
            self.fig, 
            self.plot,
            init_func=self.init_plot, 
            blit=True
        )
        plt.show()

    def init_plot(self):
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(-1, 1)
        return self.line,

    def update(self, x, y):
        self.xdata[:-1] = self.xdata[1:]
        self.xdata[:-1] = self.xdata[1:]
        self.xdata[-1] = x
        self.ydata[-1] = y

    def plot(self, i) -> None:
        xmin, xmax = self.ax.get_xlim()
        if self.xdata[-1] >= xmax:
            self.ax.set_xlim(xmin, 2*xmax)
            self.ax.figure.canvas.draw()
        self.line.set_data(self.xdata, self.ydata)
        return self.line,
     