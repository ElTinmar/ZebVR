from typing import Tuple, Dict
from .visual_stim import VisualStim
from vispy import gloo, app
from multiprocessing import Value

# TODO add transformation from camera coords to proj coords

VERT_SHADER_PHOTOTAXIS = """
attribute vec2 a_position;
attribute vec2 a_resolution;
attribute float a_time;

attribute vec4 a_color;
varying vec2 v_resolution;
varying float v_time;
varying vec4 v_color;
attribute vec2 a_fish_orientation;
attribute vec2 a_fish_centroid; 
varying vec2 v_fish_orientation;
varying vec2 v_fish_centroid;
void main()
{
    gl_Position = vec4(a_position, 0.0, 1.0);
    v_fish_orientation = a_fish_orientation;
    v_fish_centroid = a_fish_centroid;
    v_color = a_color;
    v_resolution = a_resolution;
    v_time = a_time;
} 
"""

# Fragment Shaders have the following built-in input variables. 
# in vec4 gl_FragCoord;
# in bool gl_FrontFacing;
# in vec2 gl_PointCoord;

FRAG_SHADER_PHOTOTAXIS = """
varying vec2 v_fish_orientation;
varying vec2 v_fish_centroid;
varying vec2 v_resolution;
varying float v_time;
varying vec4 v_color;

void main()
{
    if ( dot(gl_FragCoord.xy-v_fish_centroid, v_fish_orientation)>0 ) {
        gl_FragColor = v_color;
    } 
}
"""

class Phototaxis(VisualStim):

    def __init__(
            self,  
            window_size: Tuple[int, int], 
            window_position: Tuple[int, int], 
            color: Tuple[int, int, int, int],
            window_decoration: bool = True
        ) -> None:

        super().__init__(VERT_SHADER_PHOTOTAXIS, FRAG_SHADER_PHOTOTAXIS, window_size, window_position, window_decoration)

        self.color = color
        self.fish_orientation_x = Value('d',0)
        self.fish_orientation_y = Value('d',0)
        self.fish_centroid_x = Value('d',0)
        self.fish_centroid_y = Value('d',0)
        
    def initialize(self):
        super().initialize()
               
        self.program['a_color'] = self.color
        self.program['a_fish_orientation'] = [0,0]
        self.program['a_fish_centroid'] = [0,0]
    
        self.timer = app.Timer('auto', self.on_timer)
        self.timer.start()
        self.show()

    def on_draw(self, event):
        super().on_draw(event)
        gloo.clear('black')
        self.program.draw('triangle_strip')

    def on_timer(self, event):
        self.program['a_fish_orientation'] = [self.fish_orientation_x.value, self.fish_orientation_y.value]
        self.program['a_fish_centroid'] = [self.fish_centroid_x.value, self.fish_centroid_y.value]
        self.update()

    def work(self, data: Dict) -> None:
        print(data)
        if data is not None:
            self.fish_orientation_x.value = data['orientation'][0,1]
            self.fish_orientation_y.value = data['orientation'][1,1]
            self.fish_centroid_x.value = data['centroid'][0]
            self.fish_centroid_y.value = data['centroid'][1]

    