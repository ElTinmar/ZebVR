from typing import Tuple
from .visual_stim import VisualStim
from vispy import gloo, app
from multiprocessing import Value
import time
from numpy.typing import NDArray
import numpy as np 

VERT_SHADER_PHOTOTAXIS = """
uniform mat3 u_transformation_matrix;

attribute vec2 a_position;
attribute vec2 a_resolution;
attribute float a_time;
attribute vec4 a_color;
attribute vec2 a_fish_pc2;
attribute vec2 a_fish_centroid; 

varying vec2 v_fish_orientation;
varying vec2 v_fish_centroid;
varying vec2 v_resolution;
varying float v_time;
varying vec4 v_color;

void main()
{
    vec3 fish_centroid = u_transformation_matrix * vec3(a_fish_centroid, 1.0) ;
    vec3 fish_orientation = u_transformation_matrix * vec3(a_fish_centroid+a_fish_pc2, 1.0);

    gl_Position = vec4(a_position, 0.0, 1.0);
    v_fish_centroid = fish_centroid.xy;
    v_fish_orientation = fish_orientation.xy - fish_centroid.xy;
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
// IMPORTANT NOTE: WHEN USING THE LIGHTCRAFTER @ NATIVE 1140x920
// THE ASPECT RATIO IS NOT CORRECT. THAT NEEDS TO BE TAKEN INTO
// ACCOUNT 

uniform vec2 u_pixel_scaling;

varying vec2 v_fish_orientation;
varying vec2 v_fish_centroid;
varying vec2 v_resolution;
varying float v_time;
varying vec4 v_color;

float lineSegment(vec2 p, vec2 a, vec2 b) {
    vec2 pa = p - a, ba = b - a;
    float h = clamp( dot(pa,ba)/dot(ba,ba), 0.0, 1.0 );
    return length(pa - ba*h);
}

void main()
{
    vec2 fish_ego_coords = gl_FragCoord.xy*u_pixel_scaling - v_fish_centroid;

    if ( dot(fish_ego_coords, v_fish_orientation) > 0.0 ) {
        gl_FragColor = v_color;
    } 
    
    if ( lineSegment(fish_ego_coords, vec2(0.0), 1000*v_fish_orientation) < 2) {
        gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);
    }

    if ( dot(fish_ego_coords,fish_ego_coords) < 50 ) {
        gl_FragColor = vec4(0.0,1.0,0.0,1.0);
    }
}
"""

class Phototaxis(VisualStim):

    def __init__(
            self,  
            window_size: Tuple[int, int], 
            window_position: Tuple[int, int], 
            color: Tuple[int, int, int, int],
            window_decoration: bool = True,
            transformation_matrix: NDArray = np.eye(3, dtype=np.float32),
            pixel_scaling: Tuple[float, float] = (1.0,1.0),
            refresh_rate: int = 120
        ) -> None:

        super().__init__(VERT_SHADER_PHOTOTAXIS, FRAG_SHADER_PHOTOTAXIS, window_size, window_position, window_decoration, transformation_matrix, pixel_scaling)

        self.color = color
        self.fish_orientation_x = Value('d',0)
        self.fish_orientation_y = Value('d',0)
        self.fish_centroid_x = Value('d',0)
        self.fish_centroid_y = Value('d',0)
        self.refresh_rate = refresh_rate
        
    def initialize(self):
        super().initialize()
               
        self.program['a_color'] = self.color
        self.program['a_fish_pc2'] = [0,0]
        self.program['a_fish_centroid'] = [0,0]
    
        self.timer = app.Timer(1/self.refresh_rate, self.on_timer)
        self.timer.start()
        self.show()

    def on_draw(self, event):
        super().on_draw(event)
        gloo.clear('black')
        self.program.draw('triangle_strip')

    def on_timer(self, event):
        self.program['a_fish_pc2'] = [self.fish_orientation_x.value, self.fish_orientation_y.value]
        self.program['a_fish_centroid'] = [self.fish_centroid_x.value, self.fish_centroid_y.value]
        self.update()

    def work(self, data) -> None:
        if data is not None:
            index, timestamp, centroid, heading = data
            if heading is not None:
                self.fish_orientation_x.value, self.fish_orientation_y.value = heading
                self.fish_centroid_x.value, self.fish_centroid_y.value = centroid[0]
                
            # NOTE: not quite exact, image is displayed after next timer tick and update
            print(f"{index}: latency {1e-6*(time.perf_counter_ns() - timestamp)}")
