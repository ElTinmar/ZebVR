from numpy.typing import NDArray
import numpy as np
from core.dataclasses import TrackingCollection
from core.abstractclasses import Stimulus, Projector
from numba import njit
import pyglet

@njit
def compute_image(xx,yy,centroid,heading):
    return 1.0*(((xx-centroid[0]) * heading[0,1] + (yy-centroid[1]) * heading[1,1]) > 0)

def get_polygon_coord(centroid, heading):
    pass
    
class Phototaxis(Stimulus, pyglet.window.Window):

    def __init__(self, screenid: int = 0) -> None:
        super().__init__()

        display = pyglet.canvas.get_display()
        screens = display.get_screens()
        self.set_fullscreen(fullscreen=True,screen=screens[screenid])
        self.batch = pyglet.graphics.Batch()
        self.poly = pyglet.shapes.Polygon(batch=self.batch)
        self.width, self.height = self.get_size()

        self.last_timestamp = 0

    def on_draw(self):
        self.clear()
        self.batch.draw()

    def create_stim_image(self, timestamp: int, parameters: TrackingCollection) -> NDArray:
        if timestamp > self.last_timestamp:
            self.last_timestamp = timestamp
            if parameters.body is not None:
                self.img = compute_image(self.grid_x,self.grid_y,parameters.body.centroid, parameters.body.heading)
            return self.img
        else:
            return None

    