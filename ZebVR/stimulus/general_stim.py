from typing import Tuple
from .visual_stim import VisualStim
from vispy import gloo, app
from multiprocessing import Value
import time
from numpy.typing import NDArray
import numpy as np 
import os

from ZebVR.config import (
    PIX_PER_MM,             
    PHOTOTAXIS_POLARITY,
    OMR_SPATIAL_FREQUENCY_DEG,
    OMR_ANGLE_DEG,
    OMR_SPEED_DEG_PER_SEC,
    OKR_SPATIAL_FREQUENCY_DEG,
    OKR_SPEED_DEG_PER_SEC,
    LOOMING_CENTER_MM,
    LOOMING_PERIOD_SEC,
    LOOMING_EXPANSION_TIME_SEC,
    LOOMING_EXPANSION_SPEED_MM_PER_SEC
)

VERT_SHADER = """
uniform mat3 u_transformation_matrix;
attribute vec2 a_position;

// tracking
attribute float a_time;
attribute vec2 a_fish_caudorostral_axis;
attribute vec2 a_fish_mediolateral_axis;
attribute vec2 a_fish_centroid; 

varying vec2 v_fish_caudorostral_axis;
varying vec2 v_fish_mediolateral_axis;
varying vec2 v_fish_centroid;
varying float v_time;

// stim parameters
attribute float a_stim_select;
attribute float a_phototaxis_polarity;
attribute float a_omr_spatial_frequency_deg;
attribute float a_omr_angle_deg;
attribute float a_omr_speed_deg_per_sec;
attribute float a_okr_spatial_frequency_deg;
attribute float a_okr_speed_deg_per_sec;
attribute vec2 a_looming_center_mm;
attribute float a_looming_period_sec;
attribute float a_looming_expansion_time_sec;
attribute float a_looming_expansion_speed_mm_per_sec;
attribute vec4 a_foreground_color;
attribute vec4 a_background_color;

varying float v_stim_select;
varying float v_phototaxis_polarity;
varying float v_omr_spatial_frequency_deg;
varying float v_omr_angle_deg;
varying float v_omr_speed_deg_per_sec;
varying float v_okr_spatial_frequency_deg;
varying float v_okr_speed_deg_per_sec;
varying vec2 v_looming_center_mm;
varying float v_looming_period_sec;
varying float v_looming_expansion_time_sec;
varying float v_looming_expansion_speed_mm_per_sec;
varying vec4 v_foreground_color;
varying vec4 v_background_color;

void main()
{
    vec3 fish_centroid = u_transformation_matrix * vec3(a_fish_centroid, 1.0) ;
    vec3 fish_caudorostral_axis = u_transformation_matrix * vec3(a_fish_centroid+a_fish_caudorostral_axis, 1.0);
    vec3 fish_mediolateral_axis = u_transformation_matrix * vec3(a_fish_centroid+a_fish_mediolateral_axis, 1.0);

    gl_Position = vec4(a_position, 0.0, 1.0);
    v_fish_centroid = fish_centroid.xy;
    v_fish_caudorostral_axis = fish_caudorostral_axis.xy - fish_centroid.xy;
    v_fish_mediolateral_axis = fish_mediolateral_axis.xy - fish_centroid.xy;
    v_time = a_time;

    v_stim_select = a_stim_select;
    v_phototaxis_polarity = a_phototaxis_polarity;
    v_omr_spatial_frequency_deg = a_omr_spatial_frequency_deg;
    v_omr_speed_deg_per_sec = a_omr_speed_deg_per_sec;
    v_omr_angle_deg = a_omr_angle_deg;
    v_okr_spatial_frequency_deg = a_okr_spatial_frequency_deg;
    v_okr_speed_deg_per_sec = a_okr_speed_deg_per_sec;
    v_looming_center_mm = a_looming_center_mm;
    v_looming_period_sec = a_looming_period_sec;
    v_looming_expansion_time_sec = a_looming_expansion_time_sec;
    v_looming_expansion_speed_mm_per_sec = a_looming_expansion_speed_mm_per_sec;
    v_foreground_color = a_foreground_color;
    v_background_color = a_background_color;
} 
"""

FRAG_SHADER = """
// Some DMD projectors with diamond pixel layouts (e.g. Lightcrafters) do not have uniform pixel spacing.
uniform vec2 u_pixel_scaling; 

// calibration
uniform float u_pix_per_mm; 

// tracking
varying vec2 v_fish_centroid;
varying vec2 v_fish_caudorostral_axis;
varying vec2 v_fish_mediolateral_axis;
varying float v_time;

// stim parameters
varying float v_stim_select;
varying float v_phototaxis_polarity;
varying float v_omr_spatial_frequency_deg;
varying float v_omr_angle_deg;
varying float v_omr_speed_deg_per_sec;
varying float v_okr_spatial_frequency_deg;
varying float v_okr_speed_deg_per_sec;
varying vec2 v_looming_center_mm;
varying float v_looming_period_sec;
varying float v_looming_expansion_time_sec;
varying float v_looming_expansion_speed_mm_per_sec;
varying vec4 v_foreground_color;
varying vec4 v_background_color;

// constants 
const float PHOTOTAXIS = 0;
const float OMR = 1;
const float OKR = 2;
const float LOOMING = 3;
const float PI=3.14159;

// helper functions
float deg2rad(float deg) {
    float rad = PI/180 * deg;
    return rad;
}

mat2 rotate2d(float angle_rad){
    return mat2(cos(angle_rad),-sin(angle_rad),
                sin(angle_rad),cos(angle_rad));
}

void main()
{
    vec2 pixel_correct_coords = gl_FragCoord.xy*u_pixel_scaling;
    mat2 change_of_basis = mat2(v_fish_caudorostral_axis, v_fish_mediolateral_axis);
    vec2 fish_ego_coords = change_of_basis*(pixel_correct_coords - v_fish_centroid);

    gl_FragColor = v_background_color;

    if v_stim_select == PHOTOTAXIS {
        if ( v_phototaxis_polarity * fish_ego_coords.x ) > 0.0 ) {
            gl_FragColor = v_foreground_color;
        } 
    }

    if v_stim_select == OMR {
        float phase = deg2rad(v_omr_speed_deg_per_sec)*v_time;
        vec2 orientation_vector = rotate2d(deg2rad(v_omr_angle_deg)) * vec2(0,1);
        float angle = deg2rad(v_omr_spatial_frequency_deg)*dot(fish_ego_coords, orientation_vector);
        if (sin(angle+phase) > 0.0) {
            gl_FragColor = v_foreground_color;
        } 
    }

    if v_stim_select == OKR {
        float angle = atan(fish_ego_coords.y, fish_ego_coords.x);
        float phase = deg2rad(v_speed_deg_per_sec)*v_time;
        float freq = deg2rad(v_spatial_frequency_deg);
        if (mod(angle+phase,freq) > freq/2) {
            gl_FragColor = v_foreground_color;
        } 
    }

    if v_stim_select == LOOMING {
        float rel_time = mod(v_time,v_looming_period_sec); 
        float looming_on = float(rel_time<=v_looming_expansion_time_sec);
        if (rel_time <= v_looming_period_sec/2) { 
            if (distance(fish_ego_coords, v_looming_center_mm) <= u_pix_per_mm*v_looming_expansion_speed_mm_per_sec*rel_time*looming_on)
            {
                gl_FragColor = v_foreground_color;
            }
        }
    } 
}
"""

class GeneralStim(VisualStim):

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
            pix_per_mm: float = PIX_PER_MM,
            stim_select: int = 0,
            phototaxis_polarity: int = PHOTOTAXIS_POLARITY,
            omr_spatial_frequency_deg: float = OMR_SPATIAL_FREQUENCY_DEG,
            omr_angle_deg: float = OMR_ANGLE_DEG,
            omr_speed_deg_per_sec: float = OMR_SPEED_DEG_PER_SEC,
            okr_spatial_frequency_deg: float = OKR_SPATIAL_FREQUENCY_DEG,
            okr_speed_deg_per_sec: float = OKR_SPEED_DEG_PER_SEC,
            looming_center_mm: Tuple = LOOMING_CENTER_MM,
            looming_period_sec: float = LOOMING_PERIOD_SEC,
            looming_expansion_time_sec: float = LOOMING_EXPANSION_TIME_SEC,
            looming_expansion_speed_mm_per_sec: float = LOOMING_EXPANSION_SPEED_MM_PER_SEC
        ) -> None:

        super().__init__(
            vertex_shader=VERT_SHADER, 
            fragment_shader=FRAG_SHADER, 
            window_size=window_size,
            pix_per_mm=pix_per_mm, 
            window_position=window_position, 
            window_decoration=window_decoration, 
            transformation_matrix=transformation_matrix, 
            pixel_scaling=pixel_scaling, 
            vsync=vsync, 
            foreground_color=foreground_color, 
            background_color=background_color
        )

        self.fish_mediolateral_axis_x = Value('d',0)
        self.fish_mediolateral_axis_y = Value('d',0)
        self.fish_caudorostral_axis_x = Value('d',0)
        self.fish_caudorostral_axis_y = Value('d',0)
        self.fish_centroid_x = Value('d',0)
        self.fish_centroid_y = Value('d',0)
        self.index = Value('L',0)
        self.timestamp = Value('f',0)

        # stim parameters        
        self.stim_select = Value('d',stim_select) 
        self.phototaxis_polarity = Value('d',phototaxis_polarity) 
        self.omr_spatial_frequency_deg = Value('f',omr_spatial_frequency_deg)
        self.omr_angle_deg = Value('f',omr_angle_deg)
        self.omr_speed_deg_per_sec = Value('f',omr_speed_deg_per_sec)
        self.okr_spatial_frequency_deg = Value('f',okr_spatial_frequency_deg)
        self.okr_speed_deg_per_sec = Value('f',okr_speed_deg_per_sec)
        self.looming_center_mm_x = Value('f',looming_center_mm[0])
        self.looming_center_mm_y = Value('f',looming_center_mm[1])
        self.looming_period_sec = Value('f',looming_period_sec)
        self.looming_expansion_time_sec = Value('f',looming_expansion_time_sec)
        self.looming_expansion_speed_mm_per_sec = Value('f',looming_expansion_speed_mm_per_sec)
        
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
               
        self.program['a_fish_caudorostral_axis'] = [0,0]
        self.program['a_fish_mediolateral_axis'] = [0,0]
        self.program['a_fish_centroid'] = [0,0]
        self.program['a_stim_select'] = self.stim_select.value
        self.program['a_phototaxis_polarity'] = self.phototaxis_polarity.value
        self.program['a_omr_spatial_frequency_deg'] = self.omr_spatial_frequency_deg.value
        self.program['a_omr_angle_deg'] = self.omr_angle_deg.value
        self.program['a_omr_speed_deg_per_sec'] = self.omr_speed_deg_per_sec.value
        self.program['a_okr_spatial_frequency_deg'] = self.okr_spatial_frequency_deg.value
        self.program['a_okr_speed_deg_per_sec'] = self.okr_speed_deg_per_sec.value
        self.program['a_looming_center_mm'] = [self.looming_center_mm_x.value, self.looming_center_mm_y.value]
        self.program['a_looming_period_sec'] = self.looming_period_sec.value
        self.program['a_looming_expansion_time_sec'] = self.looming_expansion_time_sec.value
        self.program['a_looming_expansion_speed_mm_per_sec'] = self.looming_expansion_speed_mm_per_sec.value

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

        self.program['a_time'] = t_local
        self.program['a_fish_caudorostral_axis'] = [self.fish_caudorostral_axis_x.value, self.fish_caudorostral_axis_y.value]
        self.program['a_fish_mediolateral_axis'] = [self.fish_mediolateral_axis_x.value, self.fish_mediolateral_axis_y.value]
        self.program['a_fish_centroid'] = [self.fish_centroid_x.value, self.fish_centroid_y.value]
        self.program['a_stim_select'] = self.stim_select.value
        self.program['a_phototaxis_polarity'] = self.phototaxis_polarity.value
        self.program['a_omr_spatial_frequency_deg'] = self.omr_spatial_frequency_deg.value
        self.program['a_omr_angle_deg'] = self.omr_angle_deg.value
        self.program['a_omr_speed_deg_per_sec'] = self.omr_speed_deg_per_sec.value
        self.program['a_okr_spatial_frequency_deg'] = self.okr_spatial_frequency_deg.value
        self.program['a_okr_speed_deg_per_sec'] = self.okr_speed_deg_per_sec.value
        self.program['a_looming_center_mm'] = [self.looming_center_mm_x.value, self.looming_center_mm_y.value]
        self.program['a_looming_period_sec'] = self.looming_period_sec.value
        self.program['a_looming_expansion_time_sec'] = self.looming_expansion_time_sec.value
        self.program['a_looming_expansion_speed_mm_per_sec'] = self.looming_expansion_speed_mm_per_sec.value

        self.update()
        self.fd.write(f'{t_display},{self.index.value},{1e-6*(t_display - self.timestamp.value)},{self.fish_centroid_x.value},{self.fish_centroid_y.value},{self.fish_mediolateral_axis_x.value},{self.fish_mediolateral_axis_y.value},{t_local}\n')

    def process_data(self, data) -> None:
        if data is not None:
            index, timestamp, centroid, heading = data
            if centroid is not None:
                self.index.value = index
                self.timestamp.value = timestamp
                self.fish_caudorostral_axis_x.value, self.fish_caudorostral_axis_y.value = heading[:,0]
                self.fish_mediolateral_axis_x.value, self.fish_mediolateral_axis_y.value = heading[:,1]
                self.fish_centroid_x.value, self.fish_centroid_y.value = centroid
                
            print(f"{index}: latency {1e-6*(time.perf_counter_ns() - timestamp)}")

    def process_metadata(self, metadata) -> None:
        control = metadata['visual_stim_control']
        if control is not None:
            self.stim_select.value = control['stim_select']
            self.phototaxis_polarity.value = control['phototaxis_polarity']
            self.omr_spatial_frequency_deg.value = control['omr_spatial_frequency_deg']
            self.omr_angle_deg.value = control['omr_angle_deg']
            self.omr_speed_deg_per_sec.value = control['omr_speed_deg_per_sec']
            self.okr_spatial_frequency_deg.value = control['okr_spatial_frequency_deg']
            self.okr_speed_deg_per_sec.value = control['okr_speed_deg_per_sec']
            self.looming_center_mm_x.value = control['looming_center_mm_x']
            self.looming_center_mm_y.value = control['looming_center_mm_y']
            self.looming_period_sec.value = control['looming_period_sec']
            self.looming_expansion_time_sec.value = control['looming_expansion_time_sec']
            self.looming_expansion_speed_mm_per_sec.value = control['looming_expansion_speed_mm_per_sec']