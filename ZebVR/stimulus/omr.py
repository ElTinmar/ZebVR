from typing import Tuple
from .visual_stim import VisualStim
from vispy import gloo, app
from multiprocessing import Value
import time
from numpy.typing import NDArray
import numpy as np 
import os

VERT_SHADER_OMR = """
uniform mat3 u_transformation_matrix;

attribute vec2 a_position;
attribute float a_darkleft;
attribute vec2 a_resolution;
attribute float a_time;
attribute vec4 a_foreground_color;
attribute vec4 a_background_color;
attribute vec2 a_fish_pc2;
attribute vec2 a_fish_centroid; 
attribute float a_spatial_frequency_deg;
attribute float a_grating_speed_deg_per_sec;

varying vec2 v_fish_orientation;
varying vec2 v_fish_centroid;
varying vec2 v_resolution;
varying float v_time;
varying vec4 v_foreground_color;
varying vec4 v_background_color;
varying float v_spatial_frequency_deg;
varying float v_grating_speed_deg_per_sec;

void main()
{
    vec3 fish_centroid = u_transformation_matrix * vec3(a_fish_centroid, 1.0) ;
    vec3 fish_orientation = u_transformation_matrix * vec3(a_fish_centroid+a_fish_pc2, 1.0);

    gl_Position = vec4(a_position, 0.0, 1.0);
    v_fish_centroid = fish_centroid.xy;
    v_fish_orientation = fish_orientation.xy - fish_centroid.xy;
    v_foreground_color = a_foreground_color;
    v_background_color = a_background_color;
    v_resolution = a_resolution;
    v_time = a_time;
    v_spatial_frequency_deg = a_spatial_frequency_deg;
    v_grating_speed_deg_per_sec = a_grating_speed_deg_per_sec;
} 
"""

# Fragment Shaders have the following built-in input variables. 
# in vec4 gl_FragCoord;
# in bool gl_FrontFacing;
# in vec2 gl_PointCoord;

FRAG_SHADER_OMR = """
uniform vec2 u_pixel_scaling; 

varying vec2 v_fish_orientation;
varying vec2 v_fish_centroid;
varying vec2 v_resolution;
varying float v_time;
varying vec4 v_foreground_color;
varying vec4 v_background_color;
varying float v_spatial_frequency_deg;
varying float v_grating_speed_deg_per_sec;

void main()
{
    float PI=3.14159;
    vec2 fish_ego_coords = gl_FragCoord.xy*u_pixel_scaling - v_fish_centroid;

    gl_FragColor = v_background_color;
    float phase = PI/180*v_grating_speed_deg_per_sec*v_time;
    float angle = PI/180*v_spatial_frequency_deg*dot(fish_ego_coords, v_fish_orientation);
    if (sin(angle+phase) > 0.0) {
        gl_FragColor = v_foreground_color;
    } 
}
"""

class OMR(VisualStim):

    def __init__(
            self,  
            window_size: Tuple[int, int], 
            window_position: Tuple[int, int], 
            foreground_color: Tuple[float, float, float, float] = (1.0,0,0,1.0),
            background_color: Tuple[float, float, float, float] = (0,0,0,1.0),            
            window_decoration: bool = True,
            transformation_matrix: NDArray = np.eye(3, dtype=np.float32),
            pixel_scaling: Tuple[float, float] = (1.0,1.0),
            refresh_rate: int = 120,
            vsync: bool = True,
            timings_file: str = 'display_timings.csv',
            spatial_frequency_deg: float = 90,
            grating_speed_deg_per_sec: float = 180,
        ) -> None:

        super().__init__(
            VERT_SHADER_OMR, 
            FRAG_SHADER_OMR, 
            window_size, 
            window_position, 
            window_decoration, 
            transformation_matrix, 
            pixel_scaling, 
            vsync, 
            foreground_color, 
            background_color
        )

        self.fish_orientation_x = Value('d',0)
        self.fish_orientation_y = Value('d',0)
        self.fish_centroid_x = Value('d',0)
        self.fish_centroid_y = Value('d',0)
        self.index = Value('L',0)
        self.timestamp = Value('f',0)
        self.spatial_frequency_deg = Value('d',spatial_frequency_deg)
        self.grating_speed_deg_per_sec = Value('d',grating_speed_deg_per_sec)
        self.refresh_rate = refresh_rate
        self.fd = None
        self.tstart = 0

        if os.path.exists(timings_file):
            prefix, ext = os.path.splitext(timings_file)
            timings_file = prefix + time.strftime('_%a_%d_%b_%Y_%Hh%Mmin%Ssec') + ext

        self.timings_file = timings_file


    def initialize(self):
        super().initialize()

        self.fd = open(self.timings_file, 'w')
        # write csv headers
        self.fd.write('t_display,image_index,latency,centroid_x,centroid_y,pc2_x,pc2_y,t_local\n')
               
        self.program['a_fish_pc2'] = [0,0]
        self.program['a_fish_centroid'] = [0,0]
        self.program['a_spatial_frequency_deg'] = self.spatial_frequency_deg.value
        self.program['a_grating_speed_deg_per_sec'] = self.grating_speed_deg_per_sec.value
        self.timer = app.Timer(1/self.refresh_rate, self.on_timer)
        self.timer.start()
        self.show()

    def cleanup(self):
        super().cleanup()
        self.fd.close()

    def on_draw(self, event):
        super().on_draw(event)
        gloo.clear('black')
        self.program.draw('triangle_strip')

    def on_timer(self, event):
        if self.tstart == 0:
            self.tstart = time.perf_counter_ns()

        t_display = time.perf_counter_ns()
        t_local = 1e-9*(t_display - self.tstart)
        self.program['a_fish_pc2'] = [self.fish_orientation_x.value, self.fish_orientation_y.value]
        self.program['a_fish_centroid'] = [self.fish_centroid_x.value, self.fish_centroid_y.value]
        self.program['a_time'] = t_local
        self.program['a_spatial_frequency_deg'] = self.spatial_frequency_deg.value
        self.program['a_grating_speed_deg_per_sec'] = self.grating_speed_deg_per_sec.value
        self.update()
        self.fd.write(f'{t_display},{self.index.value},{1e-6*(t_display - self.timestamp.value)},{self.fish_centroid_x.value},{self.fish_centroid_y.value},{self.fish_orientation_x.value},{self.fish_orientation_y.value},{t_local}\n')

    def process_data(self, data) -> None:
        if data is not None:
            index, timestamp, centroid, heading = data
            if heading is not None:
                self.fish_orientation_x.value, self.fish_orientation_y.value = heading
                self.fish_centroid_x.value, self.fish_centroid_y.value = centroid[0]
                self.index.value = index
                self.timestamp.value = timestamp
                
            print(f"{index}: latency {1e-6*(time.perf_counter_ns() - timestamp)}")

    def process_metadata(self, metadata) -> None:
        control = metadata['visual_stim_control']
        if control is not None:
            self.spatial_frequency_deg.value = control['spatial_frequency_deg']
            self.grating_speed_deg_per_sec.value = control['grating_speed_deg_per_sec']