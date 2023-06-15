from numpy.typing import NDArray
from core.dataclasses import TrackingCollection
from core.abstractclasses import Stimulus
import numpy as np
from psychopy import visual
from functools import cmp_to_key

class Phototaxis(Stimulus):

    def __init__(self, screenid: int = 0) -> None:
        super().__init__()
        self.screenid = screenid

    def init_window(self):
        self.window = visual.Window(
            fullscr = True, 
            screen = self.screenid, 
            units='pix',
            colorSpace = 'rgb255'
        )
        self.w, self.h = self.window.size
        
    def close_window(self):
        self.window.close()

    def project(self, parameters: TrackingCollection) -> None:
        if parameters.body is not None:
            vertices = self.create_shape(parameters.body.centroid, parameters.body.heading)
            shape = visual.shape.ShapeStim(
                self.window, 
                units='pix', 
                vertices=vertices, 
                fillColor=[255,255,255],
                lineColor=None,
                pos=[-self.w//2, -self.h//2]
            )
            shape.draw()
            self.window.flip()
    
    def create_shape(self, centroid, heading) -> NDArray:
        vertices = []

        # add line intersection
        if heading[0,1] != 0:
            for y in [0,self.h]:
                x = 1/heading[0,1] * (centroid[0]*heading[0,1] - (y - centroid[1])*heading[1,1])
                if 0 <= x <= self.w:
                    vertices.append([x, y])
        
        if heading[1,1] != 0:
            for x in [0,self.w]:
                y = 1/heading[1,1] * (centroid[1]*heading[1,1] - (x - centroid[0])*heading[0,1])
                if 0 <= y <= self.h:
                    vertices.append([x, y])

        def compare(point1, point2):
            v1 = point1-centroid
            v2 = point2-centroid
            cross = np.cross(v1,v2)
            return np.sign(cross)

        # check window corners
        for x in [0,self.w]:
            for y in [0,self.h]:
                if np.dot((x-centroid[0],y-centroid[1]),heading[:,1]) > 0:
                    vertices.append([x, y])

        return sorted(vertices, key=cmp_to_key(compare))

    