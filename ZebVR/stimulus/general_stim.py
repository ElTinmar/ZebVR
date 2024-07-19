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
attribute vec2 a_fish_caudorostral_axis;
attribute vec2 a_fish_mediolateral_axis;
attribute vec2 a_fish_centroid; 

varying vec2 v_fish_caudorostral_axis;
varying vec2 v_fish_mediolateral_axis;
varying vec2 v_fish_centroid;

void main()
{
    vec3 fish_centroid = u_transformation_matrix * vec3(a_fish_centroid, 1.0) ;
    vec3 fish_caudorostral_axis = u_transformation_matrix * vec3(a_fish_centroid+a_fish_caudorostral_axis, 1.0);
    vec3 fish_mediolateral_axis = u_transformation_matrix * vec3(a_fish_centroid+a_fish_mediolateral_axis, 1.0);

    gl_Position = vec4(a_position, 0.0, 1.0);
    v_fish_centroid = fish_centroid.xy;
    v_fish_caudorostral_axis = fish_caudorostral_axis.xy - fish_centroid.xy;
    v_fish_mediolateral_axis = fish_mediolateral_axis.xy - fish_centroid.xy;
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
uniform float u_time;

// stim parameters
uniform vec4 u_foreground_color;
uniform vec4 u_background_color;
uniform float u_stim_select;
uniform float u_phototaxis_polarity;
uniform float u_omr_spatial_frequency_deg;
uniform float u_omr_angle_deg;
uniform float u_omr_speed_deg_per_sec;
uniform float u_okr_spatial_frequency_deg;
uniform float u_okr_speed_deg_per_sec;
uniform vec2 u_looming_center_mm;
uniform float u_looming_period_sec;
uniform float u_looming_expansion_time_sec;
uniform float u_looming_expansion_speed_mm_per_sec;

// constants 
const int DARK = 0;
const int BRIGHT = 1;
const int PHOTOTAXIS = 2;
const int OMR = 3;
const int OKR = 4;
const int LOOMING = 5;
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
    
    gl_FragColor = u_background_color;

    if (u_stim_select == DARK) {
        gl_FragColor = u_background_color;
    }

    if (u_stim_select == BRIGHT) {
        gl_FragColor = u_foreground_color;
    }

    if (u_stim_select == PHOTOTAXIS) {
        if ( u_phototaxis_polarity * fish_ego_coords.x > 0.0 ) {
            gl_FragColor = u_foreground_color;
        } 
    }

    if (u_stim_select == OMR) {
        vec2 orientation_vector = rotate2d(deg2rad(u_omr_angle_deg))*vec2(0,1);
        float angle = deg2rad(u_omr_spatial_frequency_deg)*dot(fish_ego_coords, orientation_vector);
        float phase = deg2rad(u_omr_speed_deg_per_sec)*u_time;
        if ( sin(angle+phase) > 0.0 ) {
            gl_FragColor = u_foreground_color;
        } 
    }

    if (u_stim_select == OKR) {
        float freq = deg2rad(u_okr_spatial_frequency_deg);
        float angle = atan(fish_ego_coords.y, fish_ego_coords.x);
        float phase = deg2rad(u_okr_speed_deg_per_sec)*u_time;
        if ( mod(angle+phase, freq) > freq/2 ) {
            gl_FragColor = u_foreground_color;
        } 
    }

    if (u_stim_select == LOOMING) {
        float rel_time = mod(u_time, u_looming_period_sec); 
        float looming_on = float(rel_time<=u_looming_expansion_time_sec);
        if ( rel_time <= u_looming_period_sec/2 ) { 
            if ( distance(fish_ego_coords, u_looming_center_mm) <= u_pix_per_mm*u_looming_expansion_speed_mm_per_sec*rel_time*looming_on )
            {
                gl_FragColor = u_foreground_color;
            }
        }
    } 
}
"""

#TODO add more tracking data (eyes + tail)
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
            pix_per_mm: float = PIX_PER_MM,
            refresh_rate: int = 120,
            vsync: bool = True,
            timings_file: str = 'display_timings.csv',
            stim_select: float = 0,
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
            window_position=window_position, 
            pix_per_mm=pix_per_mm, 
            window_decoration=window_decoration, 
            transformation_matrix=transformation_matrix, 
            pixel_scaling=pixel_scaling, 
            vsync=vsync
        )

        self.foreground_color = foreground_color
        self.background_color = background_color

        self.index = Value('L', 0)
        self.timestamp = Value('f', 0)
        self.fish_mediolateral_axis_x = Value('d', 0)
        self.fish_mediolateral_axis_y = Value('d', 0)
        self.fish_caudorostral_axis_x = Value('d', 0)
        self.fish_caudorostral_axis_y = Value('d', 0)
        self.fish_centroid_x = Value('d', 0)
        self.fish_centroid_y = Value('d', 0)

        # stim parameters        
        self.stim_select = Value('d', stim_select) 
        self.phototaxis_polarity = Value('d', phototaxis_polarity) 
        self.omr_spatial_frequency_deg = Value('d', omr_spatial_frequency_deg)
        self.omr_angle_deg = Value('d', omr_angle_deg)
        self.omr_speed_deg_per_sec = Value('d', omr_speed_deg_per_sec)
        self.okr_spatial_frequency_deg = Value('d', okr_spatial_frequency_deg)
        self.okr_speed_deg_per_sec = Value('d', okr_speed_deg_per_sec)
        self.looming_center_mm_x = Value('d', looming_center_mm[0])
        self.looming_center_mm_y = Value('d', looming_center_mm[1])
        self.looming_period_sec = Value('d', looming_period_sec)
        self.looming_expansion_time_sec = Value('d', looming_expansion_time_sec)
        self.looming_expansion_speed_mm_per_sec = Value('d', looming_expansion_speed_mm_per_sec)
        
        self.refresh_rate = refresh_rate
        self.fd = None
        self.tstart = 0
        
        prefix, ext = os.path.splitext(timings_file)
        timings_file = prefix + time.strftime('_%a_%d_%b_%Y_%Hh%Mmin%Ssec') + ext
        while os.path.exists(timings_file):
            time.sleep(1)
            timings_file = prefix + time.strftime('_%a_%d_%b_%Y_%Hh%Mmin%Ssec') + ext
            
        self.timings_file = timings_file

    def initialize(self):
        super().initialize()

        # write csv headers
        self.fd = open(self.timings_file, 'w')
        headers = (
            't_display',
            't_local',
            'image_index',
            'latency',
            'centroid_x',
            'centroid_y',
            'pc1_x',
            'pc1_y',
            'pc2_x',
            'pc2_y',
            'stim_id',
            'phototaxis_polarity',
            'omr_spatial_frequency_deg',
            'omr_angle_deg',
            'omr_speed_deg_per_sec',
            'okr_speed_deg_per_sec',
            'looming_center_mm_x',
            'looming_center_mm_y',
            'looming_period_sec',
            'looming_expansion_time_sec',
            'looming_expansion_speed_mm_per_sec'
        )
        self.fd.write(','.join(headers) + '\n')
        
        self.program['a_fish_caudorostral_axis'] = [0,0]
        self.program['a_fish_mediolateral_axis'] = [0,0]
        self.program['a_fish_centroid'] = [0,0]
        self.program['u_foreground_color'] = self.foreground_color
        self.program['u_background_color'] = self.background_color
        self.program['u_stim_select'] = self.stim_select.value
        self.program['u_phototaxis_polarity'] = self.phototaxis_polarity.value
        self.program['u_omr_spatial_frequency_deg'] = self.omr_spatial_frequency_deg.value
        self.program['u_omr_angle_deg'] = self.omr_angle_deg.value
        self.program['u_omr_speed_deg_per_sec'] = self.omr_speed_deg_per_sec.value
        self.program['u_okr_spatial_frequency_deg'] = self.okr_spatial_frequency_deg.value
        self.program['u_okr_speed_deg_per_sec'] = self.okr_speed_deg_per_sec.value
        self.program['u_looming_center_mm'] = [self.looming_center_mm_x.value, self.looming_center_mm_y.value]
        self.program['u_looming_period_sec'] = self.looming_period_sec.value
        self.program['u_looming_expansion_time_sec'] = self.looming_expansion_time_sec.value
        self.program['u_looming_expansion_speed_mm_per_sec'] = self.looming_expansion_speed_mm_per_sec.value

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

        self.program['a_fish_caudorostral_axis'] = [self.fish_caudorostral_axis_x.value, self.fish_caudorostral_axis_y.value]
        self.program['a_fish_mediolateral_axis'] = [self.fish_mediolateral_axis_x.value, self.fish_mediolateral_axis_y.value]
        self.program['a_fish_centroid'] = [self.fish_centroid_x.value, self.fish_centroid_y.value]
        self.program['u_time'] = t_local
        self.program['u_stim_select'] = self.stim_select.value
        self.program['u_phototaxis_polarity'] = self.phototaxis_polarity.value
        self.program['u_omr_spatial_frequency_deg'] = self.omr_spatial_frequency_deg.value
        self.program['u_omr_angle_deg'] = self.omr_angle_deg.value
        self.program['u_omr_speed_deg_per_sec'] = self.omr_speed_deg_per_sec.value
        self.program['u_okr_spatial_frequency_deg'] = self.okr_spatial_frequency_deg.value
        self.program['u_okr_speed_deg_per_sec'] = self.okr_speed_deg_per_sec.value
        self.program['u_looming_center_mm'] = [self.looming_center_mm_x.value, self.looming_center_mm_y.value]
        self.program['u_looming_period_sec'] = self.looming_period_sec.value
        self.program['u_looming_expansion_time_sec'] = self.looming_expansion_time_sec.value
        self.program['u_looming_expansion_speed_mm_per_sec'] = self.looming_expansion_speed_mm_per_sec.value

        self.update()

        row = (
            f'{t_display}',
            f'{t_local}',
            f'{self.index.value}',
            f'{1e-6*(t_display - self.timestamp.value)}',
            f'{self.fish_centroid_x.value}',
            f'{self.fish_centroid_y.value}',
            f'{self.fish_caudorostral_axis_x.value}',
            f'{self.fish_caudorostral_axis_y.value}',
            f'{self.fish_mediolateral_axis_x.value}',
            f'{self.fish_mediolateral_axis_y.value}',
            f'{self.stim_select.value}',
            f'{self.phototaxis_polarity.value}',
            f'{self.omr_spatial_frequency_deg.value}',
            f'{self.omr_angle_deg.value}',
            f'{self.omr_speed_deg_per_sec.value}',
            f'{self.okr_spatial_frequency_deg.value}',
            f'{self.okr_speed_deg_per_sec.value}',
            f'{self.looming_center_mm_x.value}',
            f'{self.looming_center_mm_y.value}',
            f'{self.looming_period_sec.value}',
            f'{self.looming_expansion_time_sec.value}',
            f'{self.looming_expansion_speed_mm_per_sec.value}'
        )
        self.fd.write(','.join(row) + '\n')

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