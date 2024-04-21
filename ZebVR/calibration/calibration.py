from vispy import gloo, app
from numpy.typing import NDArray
import numpy as np 
from typing import Tuple
import sys

VERT_SHADER_CALIBRATION = """
attribute float a_radius;
attribute vec2 a_point;
attribute vec2 a_position;

varying vec2 v_point;
varying float v_radius;

void main()
{
    gl_Position = vec4(a_position, 0.0, 1.0);
    v_point = a_point;
    v_radius = u_radius;
} 
"""

FRAG_SHADER_CALIBRATION = """
varying vec2 v_point;
varying float v_radius;

void main()
{
    if (distance(gl_FragCoord.xy,v_point) <= v_radius) {
        gl_FragColor = vec4(1.0,1.0,1.0,1.0);
    }
}
"""

class Projector(app.Canvas):

    def __init__(
            self, 
            window_size: Tuple[int, int] = (1280, 720),
            window_position: Tuple[int, int] = (0,0),
            window_decoration: bool = False,
            radius: int = 10
        ) -> None:
            
            self.window_size = window_size
            self.window_position = window_position
            self.window_decoration = window_decoration 
            self.radius = radius

    def initialize(self):
        # this needs to happen in the process where the window is displayed

        app.Canvas.__init__(
             self, 
             size=self.window_size, 
             decorate=self.window_decoration, 
             position=self.window_position, 
             keys='interactive')

        self.program = gloo.Program(VERT_SHADER_CALIBRATION, FRAG_SHADER_CALIBRATION)

        # set attributes, these must be present in the vertex shader
        self.program['a_radius'] = self.radius
        self.program['a_point'] =  [-1, -1]
        self.program['a_position'] = [(-1, -1), (-1, +1),
                                    (+1, -1), (+1, +1)]

        self.show()

    def on_draw(self, event):
        super().on_draw(event)
        gloo.clear('black')
        self.program.draw('triangle_strip')

    def draw_point(self, x: int, y: int):
        self.program['a_point'] = [x,y]
        self.update()

if __name__ == '__main__':
    proj = Projector()
    if sys.flags.interactive != 1:
        app.run()
