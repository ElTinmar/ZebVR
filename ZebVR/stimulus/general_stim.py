from typing import List, Tuple, Dict, Sequence
from .visual_stim import VisualStim
from vispy import gloo, app
from multiprocessing import RawValue, RawArray
import numpy as np 
from numpy.typing import NDArray
from dataclasses import dataclass
from geometry import AffineTransform2D
from ZebVR import MAX_PREY
from ZebVR.protocol import DEFAULT, Stim, VISUAL_STIMS
import cv2
from ZebVR.utils import SharedString, get_time_ns
import queue
from ctypes import c_bool, c_double, c_ulong

@dataclass
class SharedFishState:
    num_tail_points_interp: int

    def __post_init__(self):
        self.fish_mediolateral_axis = RawArray('f', [0, 0])
        self.fish_caudorostral_axis = RawArray('f', [0, 0])
        self.fish_centroid = RawArray('f', [0, 0])
        self.left_eye_centroid = RawArray('f', [0, 0])
        self.left_eye_angle = RawValue('f', 0)
        self.right_eye_centroid = RawArray('f', [0, 0])
        self.right_eye_angle = RawValue('f', 0)
        self.tail_points = RawArray('f', 2*self.num_tail_points_interp)

class SharedStimParameters:
    # TODO add index of fish to follow?

    def __init__(self):
        
        self.stim_change_counter = RawValue(c_double, 0) 
        self.start_time_sec = RawValue(c_double, 0) 
        self.stim_select = RawValue(c_double, Stim.DARK) 
        self.foreground_color = RawArray(c_double, DEFAULT['foreground_color'])
        self.background_color = RawArray(c_double, DEFAULT['background_color'])
        self.closed_loop = RawValue(c_bool, DEFAULT['closed_loop'])
        self.phototaxis_polarity = RawValue(c_double, DEFAULT['phototaxis_polarity']) 
        self.omr_spatial_period_mm = RawValue(c_double, DEFAULT['omr_spatial_period_mm'])
        self.omr_angle_deg = RawValue(c_double, DEFAULT['omr_angle_deg'])
        self.omr_speed_mm_per_sec = RawValue(c_double, DEFAULT['omr_speed_mm_per_sec'])
        self.turing_spatial_period_mm = RawValue(c_double, DEFAULT['turing_spatial_period_mm'])
        self.turing_angle_deg = RawValue(c_double, DEFAULT['turing_angle_deg'])
        self.turing_speed_mm_per_sec = RawValue(c_double, DEFAULT['turing_speed_mm_per_sec'])
        self.turing_n_waves = RawValue(c_ulong, DEFAULT['turing_n_waves'])
        self.concentric_spatial_period_mm = RawValue(c_double, DEFAULT['concentric_spatial_period_mm'])
        self.concentric_speed_mm_per_sec = RawValue(c_double, DEFAULT['concentric_speed_mm_per_sec'])
        self.okr_spatial_frequency_deg = RawValue(c_double, DEFAULT['okr_spatial_frequency_deg'])
        self.okr_speed_deg_per_sec = RawValue(c_double, DEFAULT['okr_speed_deg_per_sec'])
        self.looming_type = RawValue(c_double, DEFAULT['looming_type'])
        self.looming_center_mm = RawArray(c_double, DEFAULT['looming_center_mm'])
        self.looming_period_sec = RawValue(c_double, DEFAULT['looming_period_sec'])
        self.looming_expansion_time_sec = RawValue(c_double, DEFAULT['looming_expansion_time_sec'])
        self.looming_expansion_speed_mm_per_sec = RawValue(c_double, DEFAULT['looming_expansion_speed_mm_per_sec'])
        self.looming_expansion_speed_deg_per_sec = RawValue(c_double, DEFAULT['looming_expansion_speed_deg_per_sec'])
        self.looming_angle_start_deg = RawValue(c_double, DEFAULT['looming_angle_start_deg'])
        self.looming_angle_stop_deg = RawValue(c_double, DEFAULT['looming_angle_stop_deg'])
        self.looming_size_to_speed_ratio_ms = RawValue(c_double, DEFAULT['looming_size_to_speed_ratio_ms'])
        self.dot_center_mm = RawArray(c_double, DEFAULT['dot_center_mm'])
        self.dot_radius_mm = RawValue(c_double, DEFAULT['dot_radius_mm'])
        self.prey_capture_type = RawValue(c_double, DEFAULT['prey_capture_type'])
        self.n_preys = RawValue(c_ulong, DEFAULT['n_preys'])
        self.prey_speed_mm_s = RawValue(c_double, DEFAULT['prey_speed_mm_s'])
        self.prey_speed_deg_s = RawValue(c_double, DEFAULT['prey_speed_deg_s'])
        self.prey_radius_mm = RawValue(c_double, DEFAULT['prey_radius_mm'])
        self.prey_trajectory_radius_mm = RawValue(c_double, DEFAULT['prey_trajectory_radius_mm'])
        self.image_path = SharedString(initializer = DEFAULT['image_path'])
        self.image_res_px_per_mm = RawValue(c_double, DEFAULT['image_res_px_per_mm'])
        self.image_offset_mm = RawArray(c_double, DEFAULT['image_offset_mm'])
        self.ramp_duration_sec = RawValue(c_double, DEFAULT['ramp_duration_sec'])
        self.ramp_powerlaw_exponent = RawValue(c_double, DEFAULT['ramp_powerlaw_exponent'])
        self.ramp_type = RawValue(c_double, DEFAULT['ramp_type'])

    def from_dict(self, d: Dict) -> None:
        
        self.stim_change_counter.value += 1 # TODO filter on VISUAL STIM only 
        self.start_time_sec.value = d.get('time_sec', 0)
        self.stim_select.value = d.get('stim_select', Stim.DARK)
        self.foreground_color[:] = d.get('foreground_color', DEFAULT['foreground_color'])
        self.background_color[:] = d.get('background_color', DEFAULT['background_color'])
        self.closed_loop.value = d.get('closed_loop', DEFAULT['closed_loop'])
        self.phototaxis_polarity.value = d.get('phototaxis_polarity', DEFAULT['phototaxis_polarity'])
        self.omr_spatial_period_mm.value = d.get('omr_spatial_period_mm', DEFAULT['omr_spatial_period_mm'])
        self.omr_angle_deg.value = d.get('omr_angle_deg', DEFAULT['omr_angle_deg'])
        self.omr_speed_mm_per_sec.value = d.get('omr_speed_mm_per_sec', DEFAULT['omr_speed_mm_per_sec'])
        self.turing_spatial_period_mm.value = d.get('turing_spatial_period_mm', DEFAULT['turing_spatial_period_mm'])
        self.turing_angle_deg.value = d.get('turing_angle_deg', DEFAULT['turing_angle_deg'])
        self.turing_speed_mm_per_sec.value = d.get('turing_speed_mm_per_sec', DEFAULT['turing_speed_mm_per_sec'])
        self.turing_n_waves.value = d.get('turing_n_waves', DEFAULT['turing_n_waves'])
        self.concentric_spatial_period_mm.value = d.get('concentric_spatial_period_mm', DEFAULT['concentric_spatial_period_mm'])
        self.concentric_speed_mm_per_sec.value = d.get('concentric_speed_mm_per_sec', DEFAULT['concentric_speed_mm_per_sec'])
        self.okr_spatial_frequency_deg.value = d.get('okr_spatial_frequency_deg', DEFAULT['okr_spatial_frequency_deg'])
        self.okr_speed_deg_per_sec.value = d.get('okr_speed_deg_per_sec', DEFAULT['okr_speed_deg_per_sec'])
        self.looming_type.value = d.get('looming_type', DEFAULT['looming_type'])
        self.looming_center_mm[:] = d.get('looming_center_mm', DEFAULT['looming_center_mm'])
        self.looming_period_sec.value = d.get('looming_period_sec', DEFAULT['looming_period_sec'])
        self.looming_expansion_time_sec.value = d.get('looming_expansion_time_sec', DEFAULT['looming_expansion_time_sec'])
        self.looming_expansion_speed_mm_per_sec.value = d.get('looming_expansion_speed_mm_per_sec', DEFAULT['looming_expansion_speed_mm_per_sec'])
        self.looming_expansion_speed_deg_per_sec.value = d.get('looming_expansion_speed_deg_per_sec', DEFAULT['looming_expansion_speed_deg_per_sec'])
        self.looming_angle_start_deg.value = d.get('looming_angle_start_deg', DEFAULT['looming_angle_start_deg'])
        self.looming_angle_stop_deg.value = d.get('looming_angle_stop_deg', DEFAULT['looming_angle_stop_deg'])
        self.looming_size_to_speed_ratio_ms.value = d.get('looming_size_to_speed_ratio_ms', DEFAULT['looming_size_to_speed_ratio_ms'])
        self.dot_center_mm[:] = d.get('dot_center_mm', DEFAULT['dot_center_mm'])
        self.dot_radius_mm.value = d.get('dot_radius_mm', DEFAULT['dot_radius_mm'])
        self.prey_capture_type.value = d.get('prey_capture_type', DEFAULT['prey_capture_type'])
        self.n_preys.value = int(d.get('n_preys', DEFAULT['n_preys']))
        self.prey_speed_mm_s.value = d.get('prey_speed_mm_s', DEFAULT['prey_speed_mm_s'])
        self.prey_speed_deg_s.value = d.get('prey_speed_deg_s', DEFAULT['prey_speed_deg_s'])
        self.prey_radius_mm.value = d.get('prey_radius_mm', DEFAULT['prey_radius_mm'])
        self.prey_trajectory_radius_mm.value = d.get('prey_trajectory_radius_mm', DEFAULT['prey_trajectory_radius_mm'])
        self.image_path.value = d.get('image_path', DEFAULT['image_path'])
        self.image_res_px_per_mm.value = d.get('image_res_px_per_mm', DEFAULT['image_res_px_per_mm'])
        self.image_offset_mm[:] = d.get('image_offset_mm', DEFAULT['image_offset_mm'])
        self.ramp_duration_sec.value = d.get('ramp_duration_sec', DEFAULT['ramp_duration_sec'])
        self.ramp_powerlaw_exponent.value = d.get('ramp_powerlaw_exponent', DEFAULT['ramp_powerlaw_exponent'])
        self.ramp_type.value = d.get('ramp_type', DEFAULT['ramp_type'])

    def to_dict(self) -> Dict: 

        res = {
            'stim_select': self.stim_select.value,
            'timestamp': get_time_ns(),
            'start_time_sec': self.start_time_sec.value,
            'foreground_color': list(self.foreground_color),
            'background_color': list(self.background_color),
            'closed_loop': self.closed_loop.value
        }

        if self.stim_select.value == Stim.PHOTOTAXIS:
            res.update({
                'phototaxis_polarity': self.phototaxis_polarity.value,
            })

        if self.stim_select.value == Stim.OMR:
            res.update({
                'omr_spatial_period_mm': self.omr_spatial_period_mm.value,
                'omr_angle_deg': self.omr_angle_deg.value,
                'omr_speed_mm_per_sec': self.omr_speed_mm_per_sec.value,
            })

        if self.stim_select.value == Stim.TURING:
            res.update({
                'turing_spatial_period_mm': self.turing_spatial_period_mm.value,
                'turing_angle_deg': self.turing_angle_deg.value,
                'turing_speed_mm_per_sec': self.turing_speed_mm_per_sec.value,
                'turing_n_waves': self.turing_n_waves.value,
            })

        if self.stim_select.value == Stim.CONCENTRIC_GRATING:
            res.update({
                'concentric_spatial_period_mm': self.concentric_spatial_period_mm.value,
                'concentric_speed_mm_per_sec': self.concentric_speed_mm_per_sec.value,
            })

        if self.stim_select.value == Stim.OKR:
            res.update({
                'okr_spatial_frequency_deg': self.okr_spatial_frequency_deg.value,
                'okr_speed_deg_per_sec': self.okr_speed_deg_per_sec.value,
            })

        if self.stim_select.value == Stim.LOOMING:
            res.update({
                'looming_type': self.looming_type.value,
                'looming_center_mm': list(self.looming_center_mm),
                'looming_period_sec': self.looming_period_sec.value,
                'looming_expansion_time_sec': self.looming_expansion_time_sec.value,
                'looming_expansion_speed_mm_per_sec': self.looming_expansion_speed_mm_per_sec.value,
                'looming_expansion_speed_deg_per_sec': self.looming_expansion_speed_deg_per_sec.value,
                'looming_angle_start_deg': self.looming_angle_start_deg.value,
                'looming_angle_stop_deg': self.looming_angle_stop_deg.value,
                'looming_size_to_speed_ratio_ms': self.looming_size_to_speed_ratio_ms.value,
            })

        if self.stim_select.value == Stim.DOT:
            res.update({
                'dot_center_mm': list(self.dot_center_mm),
                'dot_radius_mm': self.dot_radius_mm.value,
            })

        if self.stim_select.value == Stim.PREY_CAPTURE:
            res.update({
                'prey_capture_type': self.prey_capture_type.value,
                'n_preys': self.n_preys.value,
                'prey_speed_mm_s': self.prey_speed_mm_s.value,
                'prey_speed_deg_s': self.prey_speed_deg_s.value,
                'prey_radius_mm': self.prey_radius_mm.value,
                'prey_trajectory_radius_mm': self.prey_trajectory_radius_mm.value,
            })

        if self.stim_select.value == Stim.IMAGE:
            res.update({
                'image_path': self.image_path.value,
                'image_res_px_per_mm': self.image_res_px_per_mm.value,
                'image_offset_mm': list(self.image_offset_mm),
            })

        if self.stim_select.value == Stim.RAMP:
            res.update({
                'ramp_duration_sec': self.ramp_duration_sec.value,
                'ramp_powerlaw_exponent': self.ramp_powerlaw_exponent.value,
                'ramp_type': self.ramp_type.value,
            })

        return res

VERT_SHADER = """
attribute vec2 a_position;

void main()
{
    gl_Position = vec4(a_position, 0.0, 1.0);
}
"""

class GeneralStim(VisualStim):

    def __init__(
            self,  
            ROI_identities: List[Tuple[int,int,int,int]],
            window_size: Tuple[int, int], 
            window_position: Tuple[int, int], 
            camera_resolution: Tuple[int, int],
            window_decoration: bool = True,
            init_offset: Tuple[float, float] = (0.0, 0.0),
            init_heading: NDArray[np.float32] = np.array([[1.0, 0.0], [0.0, 1.0]]),
            transformation_matrix: AffineTransform2D = AffineTransform2D.identity(),
            pixel_scaling: Tuple[float, float] = (1.0,1.0),
            pix_per_mm: float = 30,
            refresh_rate: int = 120,
            vsync: bool = False,
            fullscreen: bool = True,
            num_tail_points_interp: int = 40,
            rollover_time_sec: float = 3600 # TODO add that to a gui somewhere
        ) -> None:

        self.ROI_identities = ROI_identities
        self.num_tail_points_interp = num_tail_points_interp
        self.n_animals = len(ROI_identities)
        self.rollover_time_sec = rollover_time_sec
        self._last_image_path: str = ''

        FRAG_SHADER = f"""
        // Some DMD projectors with diamond pixel layouts (e.g. Lightcrafters) do not have uniform pixel spacing.
        uniform vec2 u_pixel_scaling; 
        uniform float u_pix_per_mm; 
        uniform vec2 u_pix_per_mm_proj;
        uniform vec2 u_proj_resolution;
        uniform vec2 u_cam_resolution;
        uniform mat3 u_cam_to_proj;
        uniform mat3 u_proj_to_cam;

        // tracking : fish coordinates are already transformed in projector space
        uniform int u_n_animals;
        uniform vec2 u_fish_centroid[{self.n_animals}];
        uniform vec2 u_fish_caudorostral_axis[{self.n_animals}];
        uniform vec2 u_fish_mediolateral_axis[{self.n_animals}];
        uniform vec2 u_left_eye_centroid[{self.n_animals}]; 
        uniform float u_left_eye_angle[{self.n_animals}];
        uniform vec2 u_right_eye_centroid[{self.n_animals}];
        uniform float u_right_eye_angle[{self.n_animals}];
        uniform vec4 u_bounding_box[{self.n_animals}];
        uniform highp float u_time_s;
        uniform highp float u_start_time_s;

        // stim parameters
        uniform vec4 u_foreground_color;
        uniform vec4 u_background_color;
        uniform bool u_closed_loop;
        uniform float u_stim_select;
        uniform float u_phototaxis_polarity;
        uniform float u_omr_spatial_period_mm;
        uniform float u_omr_angle_deg;
        uniform float u_omr_speed_mm_per_sec;
        uniform float u_turing_spatial_period_mm;
        uniform float u_turing_angle_deg;
        uniform float u_turing_speed_mm_per_sec;
        uniform float u_turing_n_waves;
        uniform float u_concentric_spatial_period_mm;
        uniform float u_concentric_speed_mm_per_sec;
        uniform float u_okr_spatial_frequency_deg;
        uniform float u_okr_speed_deg_per_sec;
        uniform int u_looming_type;
        uniform vec2 u_looming_center_mm;
        uniform float u_looming_period_sec;
        uniform float u_looming_expansion_time_sec;
        uniform float u_looming_expansion_speed_mm_per_sec;
        uniform float u_looming_expansion_speed_deg_per_sec;
        uniform float u_looming_angle_start_deg;
        uniform float u_looming_angle_stop_deg;
        uniform float u_looming_size_to_speed_ratio_ms;
        uniform vec2 u_dot_center_mm;
        uniform float u_dot_radius_mm;
        uniform int u_prey_capture_type;
        uniform float u_n_preys;
        uniform float u_prey_radius_mm;
        uniform float u_prey_trajectory_radius_mm;
        uniform float u_prey_speed_mm_s;
        uniform float u_prey_speed_deg_s;
        uniform vec2 u_prey_position[{MAX_PREY}]; // in projector space
        uniform float u_prey_trajectory_angle[{MAX_PREY}];  
        uniform sampler2D u_image_texture;
        uniform vec2 u_image_size;
        uniform float u_image_res_px_per_mm;
        uniform vec2 u_image_offset_mm;
        uniform float u_ramp_duration_sec;
        uniform float u_ramp_powerlaw_exponent;
        uniform int u_ramp_type;
        
        // constants 
        const int LINEAR = 0;
        const int POWER_LAW = 1;

        const int LINEAR_RADIUS = 0;
        const int LINEAR_ANGLE = 1;
        const int CONSTANT_VELOCITY = 2;

        const int RING = 0;
        const int RANDOM_CLOUD = 1;
        
        const int DARK = 0;
        const int BRIGHT = 1;
        const int PHOTOTAXIS = 2;
        const int OMR = 3;
        const int OKR = 4;
        const int LOOMING = 5;
        const int PREY_CAPTURE = 6;
        const int CONCENTRIC_GRATING = 7;
        const int DOT = 8;
        const int IMAGE = 9;
        const int RAMP = 10;
        const int TURING = 11;

        const float PI = radians(180.0);
        """ + """

        // HELPER FUNCTIONS -------------------------------------------------------------------------

        bool is_point_in_bbox(vec2 point, vec2 minBounds, vec2 maxBounds) {
            return all(greaterThanEqual(point, minBounds)) && all(lessThanEqual(point, maxBounds));
        }

        mat2 rotate2d(float angle_rad){
            return mat2(cos(angle_rad),-sin(angle_rad),
                        sin(angle_rad),cos(angle_rad));
        }

        // pseudo-random hash
        float hash(float x){
            return fract(sin(x)*43758.5453123);
        }

        vec3 linear_to_srgb(vec3 linear)
        {
            vec3 a = 12.92 * linear;
            vec3 b = 1.055 * pow(linear, vec3(1.0 / 2.4)) - 0.055;
            return mix(a, b, step(0.0031308, linear));
        }
        vec4 linear_to_srgb(vec4 linear)
        {
            return vec4(linear_to_srgb(linear.rgb), linear.a);
        }

        // STIMULI ----------------------------------------------------------------------------------

        vec4 dark_stimulus() {
            return u_background_color;
        }

        vec4 bright_stimulus() {
            return u_foreground_color;
        }

        vec4 phototaxis_stimulus(vec2 coords_mm) {
            if ( u_phototaxis_polarity * coords_mm.x > 0.0 ) {
                return u_foreground_color;
            }
            return u_background_color;
        }

        vec4 omr_stimulus(vec2 coords_mm) {
            vec2 orientation_vector = rotate2d(radians(u_omr_angle_deg)) * vec2(0,1);
            float position_on_orientation_vector = dot(coords_mm, orientation_vector)/length(orientation_vector);
            float spatial_freq = 1/u_omr_spatial_period_mm;
            float temporal_freq = u_omr_speed_mm_per_sec/u_omr_spatial_period_mm;
            float angle = spatial_freq * position_on_orientation_vector;
            float phase = temporal_freq * u_time_s;

            if ( sin(2*PI*(angle+phase)) > 0.0 ) { 
                return u_foreground_color;
            }
            return u_background_color;
        }

        vec4 turing_stimulus(vec2 coords_mm) {
            float angle_rad = radians(u_turing_angle_deg);
            vec2 velocity = u_turing_speed_mm_per_sec * vec2(cos(angle_rad), sin(angle_rad));
            vec2 pos = coords_mm + velocity * u_time_s; 
            float k0 = 2.0 * PI / u_turing_spatial_period_mm;

            float wave_sum = 0.0;
            for(int i = 0; i < u_turing_n_waves; i++) {
                float angle = (float(i) + hash(float(i))) / float(u_turing_n_waves) * 2.0 * PI;
                float phase = hash(float(i)*12.34) * 2.0 * PI;
                vec2 dir = vec2(cos(angle), sin(angle));
                float wave = sin(k0 * dot(pos, dir) + phase);
                wave_sum += wave;
            }

            if (wave_sum > 0) {
                return u_foreground_color;
            }
            return u_background_color;
        }

        vec4 okr_stimulus(vec2 coords_mm) {
            float angular_spatial_freq = radians(u_okr_spatial_frequency_deg);
            float angular_temporal_freq = radians(u_okr_speed_deg_per_sec);   
            float angle = atan(coords_mm.y, coords_mm.x);
            float phase = angular_temporal_freq * u_time_s;

            if ( mod(angle+phase, angular_spatial_freq) > angular_spatial_freq/2 ) {
                return u_foreground_color;
            } 
            return u_background_color;
        }

        vec4 dot_stimulus(vec2 coords_mm) {
            if ( distance(coords_mm, u_dot_center_mm) <= u_dot_radius_mm) {
                return u_foreground_color;
            }
            return u_background_color;
        }

        vec4 looming_linear_radius_stimulus(vec2 coords_mm) {
            float relative_time = mod(u_time_s - u_start_time_s, u_looming_period_sec); 
            float looming_on = float(relative_time <= u_looming_expansion_time_sec);
            float looming_radius = u_looming_expansion_speed_mm_per_sec * relative_time * looming_on;
            
            if ( distance(coords_mm, u_looming_center_mm) <= looming_radius ) {
                return u_foreground_color;
            }
            return u_background_color;
        }

        vec4 looming_linear_angle_stimulus(vec2 coords_mm) {
            float relative_time = mod(u_time_s - u_start_time_s, u_looming_period_sec); 
            float looming_on = float(relative_time <= u_looming_expansion_time_sec);
            float visual_angle = radians(u_looming_expansion_speed_deg_per_sec) * relative_time * looming_on;
            float looming_radius = length(u_looming_center_mm) * tan(visual_angle/2);

            if ( distance(coords_mm, u_looming_center_mm) <= looming_radius ) {
                return u_foreground_color;
            }
            return u_background_color;
        }

        vec4 looming_constant_velocity_stimulus(vec2 coords_mm) {
            float angle_start_rad = radians(u_looming_angle_start_deg);
            float angle_stop_rad = radians(u_looming_angle_stop_deg);
            float t_0 = u_looming_size_to_speed_ratio_ms / tan(angle_start_rad/2);
            float t_f = u_looming_size_to_speed_ratio_ms / tan(angle_stop_rad/2);
            float period_ms = t_0 - t_f;
            float relative_time_ms = mod(1000*(u_time_s - u_start_time_s), period_ms); 
            float looming_radius = length(u_looming_center_mm) * u_looming_size_to_speed_ratio_ms / (t_0 - relative_time_ms);

            if ( distance(coords_mm, u_looming_center_mm) <= looming_radius ) {
                return u_foreground_color;
            }
            return u_background_color;
        }

        vec4 concentric_grating_stimulus(vec2 coords_mm) {
            float spatial_freq = 1 / u_concentric_spatial_period_mm;
            float temporal_freq = u_concentric_speed_mm_per_sec / u_concentric_spatial_period_mm;
            float distance_to_center_mm = length(coords_mm);
            float angle = spatial_freq * distance_to_center_mm;
            float phase = temporal_freq * u_time_s;

            if ( sin(2*PI*(angle+phase)) > 0.0 ) {
                return u_foreground_color;
            }
            return u_background_color;
        }

        vec4 prey_capture_ring_stimulus(vec2 coords_mm) {
            float phase = radians(u_prey_speed_deg_s) * u_time_s;

            for (int i = 0; i < u_n_preys; i++) {
                float angle = i * 2*PI/u_n_preys;      
                vec2 prey_offset = u_prey_trajectory_radius_mm * vec2(cos(angle+phase), sin(angle+phase));

                if ( distance(coords_mm, prey_offset) <= u_prey_radius_mm) {
                    return u_foreground_color;
                }
            }
            return u_background_color;
        }

        vec4 prey_capture_random_cloud_stimulus(vec2 coords_mm, vec4 bbox_mm) {
            for (int i = 0; i < u_n_preys; i++) {
                vec2 current_prey_pos_mm = u_prey_position[i] / u_pix_per_mm_proj;
                vec2 current_prey_dir = vec2(cos(u_prey_trajectory_angle[i]), sin(u_prey_trajectory_angle[i]));
                vec2 pos = mod(current_prey_pos_mm + u_time_s * u_prey_speed_mm_s * current_prey_dir, bbox_mm.zw) - bbox_mm.zw / 2.0;
                if ( distance(pos, coords_mm) <= u_prey_radius_mm ) {
                    return u_foreground_color;
                }
            }
            return u_background_color;  
        }  

        vec4 image_stimulus(vec2 coords_mm) {
            vec2 image_size_mm = u_image_size / u_image_res_px_per_mm;
            vec2 coords = 0.5 + (coords_mm - u_image_offset_mm) / image_size_mm;
            if (coords.x >= 0.0 && coords.x <= 1.0 &&
                coords.y >= 0.0 && coords.y <= 1.0) {
                return texture2D(u_image_texture, coords);
            }
            return u_background_color;
        }

        vec4 ramp_stimulus() {
            float relative_time = mod(u_time_s - u_start_time_s, u_ramp_duration_sec);
            float frac = clamp(relative_time / u_ramp_duration_sec, 0.0, 1.0);
            float ramp_value = 0.0;

            if (u_ramp_type == LINEAR) {
                ramp_value = frac;
            }

            if (u_ramp_type == POWER_LAW) {
                // Stevens' law: S = kI**a 
                float exponent = u_ramp_powerlaw_exponent;
                ramp_value = pow(frac, 1/exponent);
            }

            return mix(u_background_color, u_foreground_color, ramp_value);
        }        

        // MAIN ------------------------------------------------------------------------------------

        void main()
        {
            vec2 coordinates_centered_px;
            mat2 change_of_basis;
            vec4 camera_bbox_px;
            vec4 camera_bbox_mm;

            vec2 coordinates_px = gl_FragCoord.xy * u_pixel_scaling;
            vec2 coordinates_mm = coordinates_px / u_pix_per_mm_proj;
            vec3 camera_coordinates_px = u_proj_to_cam * vec3(coordinates_px, 1.0);
            vec2 camera_coordinates_mm = camera_coordinates_px.xy / u_pix_per_mm;

            gl_FragColor = vec4(0,0,0,1); // black outside of fish ROI

            for (int animal = 0; animal < u_n_animals; animal++) {

                // STEP 1: COMPUTE THE DIFFERENT COORDINATES SYSTEMS ----------------------------------------------------------------

                // different coordinate systems
                vec2 coordinates_centered_mm; // projector x,y coordinates. Origin: bounding box center, y axis: , x axis:  
                vec2 fish_ego_coords_mm; // fish egocentric coordinates: Origin: fish centroid, y axis: fish major axis, x axis: right
                vec2 fish_centered_coords_mm; // fish-centric coordinates: Origin: fish centroid, y axis: proj up , x axis: proj right 

                // get current bounding box center in projector space  
                camera_bbox_px = u_bounding_box[animal];
                if ( !is_point_in_bbox(camera_coordinates_px.xy, camera_bbox_px.xy, camera_bbox_px.xy+camera_bbox_px.zw) ) {
                    continue;
                }
                vec3 proj_bbox_origin = u_cam_to_proj * vec3(camera_bbox_px.xy, 1.0);
                vec3 proj_bbox_size = u_cam_to_proj * vec3(camera_bbox_px.zw, 0.0);
                vec4 proj_bbox_px = vec4(proj_bbox_origin.xy, proj_bbox_size.xy);
                vec4 proj_bbox_mm = vec4(proj_bbox_origin.xy / u_pix_per_mm_proj, proj_bbox_size.xy/ u_pix_per_mm_proj);
                vec2 proj_bbox_center_mm = proj_bbox_mm.xy + proj_bbox_mm.zw/2.0;
                coordinates_centered_mm = coordinates_mm - proj_bbox_center_mm; 

                // compute fish-centric coordinates 
                coordinates_centered_px = coordinates_px - u_fish_centroid[animal];
                change_of_basis = mat2(
                    u_fish_mediolateral_axis[animal]/length(u_fish_mediolateral_axis[animal]), 
                    u_fish_caudorostral_axis[animal]/length(u_fish_caudorostral_axis[animal])
                );
                vec2 fish_ego_coords_px = transpose(change_of_basis) * coordinates_centered_px;
                fish_ego_coords_mm = fish_ego_coords_px / u_pix_per_mm_proj;
                fish_centered_coords_mm = coordinates_centered_px / u_pix_per_mm_proj;

                // STEP 2: COMPUTE STIMULI ------------------------------------------------------------------------------------------

                // choose which coordinate system to use
                vec2 local_coordinates_mm = coordinates_centered_mm;
                if (u_closed_loop) {local_coordinates_mm = fish_ego_coords_mm;}

                // choose which stimulus to show
                gl_FragColor = u_background_color; 

                if (u_stim_select == DARK) {gl_FragColor = dark_stimulus();}
                if (u_stim_select == BRIGHT) {gl_FragColor = bright_stimulus();}
                if (u_stim_select == RAMP) {gl_FragColor = ramp_stimulus();}
                if (u_stim_select == PHOTOTAXIS) {gl_FragColor = phototaxis_stimulus(local_coordinates_mm);}
                if (u_stim_select == OMR) {gl_FragColor = omr_stimulus(local_coordinates_mm);}
                if (u_stim_select == TURING) {gl_FragColor = turing_stimulus(local_coordinates_mm);}
                if (u_stim_select == OKR) {gl_FragColor = okr_stimulus(local_coordinates_mm);}
                if (u_stim_select == DOT) {gl_FragColor = dot_stimulus(local_coordinates_mm);}
                if (u_stim_select == LOOMING) {
                    if (u_looming_type == LINEAR_RADIUS) {gl_FragColor = looming_linear_radius_stimulus(local_coordinates_mm);}
                    if (u_looming_type == LINEAR_ANGLE) {gl_FragColor = looming_linear_angle_stimulus(local_coordinates_mm);}
                    if (u_looming_type == CONSTANT_VELOCITY) {gl_FragColor = looming_constant_velocity_stimulus(local_coordinates_mm);}
                }
                if (u_stim_select == CONCENTRIC_GRATING) {gl_FragColor = concentric_grating_stimulus(local_coordinates_mm);}
                if (u_stim_select == IMAGE)  {gl_FragColor = image_stimulus(local_coordinates_mm);}
                if (u_stim_select == PREY_CAPTURE) {
                    if (u_prey_capture_type == RING) {gl_FragColor = prey_capture_ring_stimulus(local_coordinates_mm);}
                    if (u_prey_capture_type == RANDOM_CLOUD) {gl_FragColor = prey_capture_random_cloud_stimulus(local_coordinates_mm, proj_bbox_mm);}
                }
            }

            // convert to sRGB color space. Assume images already in sRGB.
            if (u_stim_select != IMAGE) {
                gl_FragColor = linear_to_srgb(gl_FragColor);
            }
        }
        """

        super().__init__(
            vertex_shader = VERT_SHADER, 
            fragment_shader = FRAG_SHADER, 
            window_size = window_size,
            window_position = window_position, 
            camera_resolution = camera_resolution,
            pix_per_mm = pix_per_mm, 
            window_decoration = window_decoration, 
            transformation_matrix = transformation_matrix, 
            pixel_scaling = pixel_scaling, 
            vsync = vsync,
            fullscreen = fullscreen
        )

        self.shared_fish_state = [SharedFishState(num_tail_points_interp) for _ in  ROI_identities]
        for fish_id, fish_state in enumerate(self.shared_fish_state):
            centroid = np.array(init_offset) + np.array(ROI_identities[fish_id][:2]) + np.array(ROI_identities[fish_id][2:])//2
            fish_state.fish_caudorostral_axis[:] = self.transformation_matrix.transform_vectors(init_heading[:,0]).squeeze()
            fish_state.fish_mediolateral_axis[:] = self.transformation_matrix.transform_vectors(init_heading[:,1]).squeeze()
            fish_state.fish_centroid[:] = self.transformation_matrix.transform_points(centroid).squeeze()

        self.shared_stim_parameters = SharedStimParameters()
        self.stim_change_counter = 0

        self.refresh_rate = refresh_rate
        self.tstart = 0


    def update_shader_variables(self, time_s: float):
        # communication between CPU and GPU for every frame drawn

        self.program['u_time_s'] = time_s

        # fish state 
        # TODO send tail data to shader?        

        self.program['u_bounding_box'] = self.ROI_identities
        
        for i in range(self.n_animals):
            self.program[f'u_fish_centroid[{i}]'] = self.shared_fish_state[i].fish_centroid[:] 
            self.program[f'u_fish_caudorostral_axis[{i}]'] = self.shared_fish_state[i].fish_caudorostral_axis[:]
            self.program[f'u_fish_mediolateral_axis[{i}]'] = self.shared_fish_state[i].fish_mediolateral_axis[:]
            self.program[f'u_left_eye_centroid[{i}]'] = self.shared_fish_state[i].left_eye_centroid[:]
            self.program[f'u_left_eye_angle[{i}]'] = self.shared_fish_state[i].left_eye_angle.value
            self.program[f'u_right_eye_centroid[{i}]'] = self.shared_fish_state[i].right_eye_centroid[:]
            self.program[f'u_right_eye_angle[{i}]'] = self.shared_fish_state[i].right_eye_angle.value
    
        # stim parameters
        self.program['u_start_time_s'] = self.shared_stim_parameters.start_time_sec.value
        self.program['u_foreground_color'] = self.shared_stim_parameters.foreground_color[:]
        self.program['u_background_color'] = self.shared_stim_parameters.background_color[:]
        self.program['u_closed_loop'] = self.shared_stim_parameters.closed_loop.value
        self.program['u_stim_select'] = self.shared_stim_parameters.stim_select.value
        self.program['u_phototaxis_polarity'] = self.shared_stim_parameters.phototaxis_polarity.value
        self.program['u_omr_spatial_period_mm'] = self.shared_stim_parameters.omr_spatial_period_mm.value
        self.program['u_omr_angle_deg'] = self.shared_stim_parameters.omr_angle_deg.value
        self.program['u_omr_speed_mm_per_sec'] = self.shared_stim_parameters.omr_speed_mm_per_sec.value
        self.program['u_turing_spatial_period_mm'] = self.shared_stim_parameters.turing_spatial_period_mm.value
        self.program['u_turing_angle_deg'] = self.shared_stim_parameters.turing_angle_deg.value
        self.program['u_turing_speed_mm_per_sec'] = self.shared_stim_parameters.turing_speed_mm_per_sec.value
        self.program['u_turing_n_waves'] = self.shared_stim_parameters.turing_n_waves.value
        self.program['u_concentric_spatial_period_mm'] = self.shared_stim_parameters.concentric_spatial_period_mm.value
        self.program['u_concentric_speed_mm_per_sec'] = self.shared_stim_parameters.concentric_speed_mm_per_sec.value
        self.program['u_okr_spatial_frequency_deg'] = self.shared_stim_parameters.okr_spatial_frequency_deg.value
        self.program['u_okr_speed_deg_per_sec'] = self.shared_stim_parameters.okr_speed_deg_per_sec.value
        self.program['u_looming_type'] = self.shared_stim_parameters.looming_type
        self.program['u_looming_center_mm'] = self.shared_stim_parameters.looming_center_mm[:]
        self.program['u_looming_period_sec'] = self.shared_stim_parameters.looming_period_sec.value
        self.program['u_looming_expansion_time_sec'] = self.shared_stim_parameters.looming_expansion_time_sec.value
        self.program['u_looming_expansion_speed_mm_per_sec'] = self.shared_stim_parameters.looming_expansion_speed_mm_per_sec.value
        self.program['u_looming_expansion_speed_deg_per_sec'] = self.shared_stim_parameters.looming_expansion_speed_deg_per_sec.value
        self.program['u_looming_angle_start_deg'] = self.shared_stim_parameters.looming_angle_start_deg.value
        self.program['u_looming_angle_stop_deg'] = self.shared_stim_parameters.looming_angle_stop_deg.value
        self.program['u_looming_size_to_speed_ratio_ms'] = self.shared_stim_parameters.looming_size_to_speed_ratio_ms.value
        self.program['u_dot_center_mm'] = self.shared_stim_parameters.dot_center_mm[:]
        self.program['u_dot_radius_mm'] = self.shared_stim_parameters.dot_radius_mm.value
        self.program['u_prey_speed_mm_s'] = self.shared_stim_parameters.prey_speed_mm_s.value
        self.program['u_prey_speed_deg_s'] = self.shared_stim_parameters.prey_speed_deg_s.value
        self.program['u_prey_radius_mm'] = self.shared_stim_parameters.prey_radius_mm.value
        self.program['u_prey_trajectory_radius_mm'] = self.shared_stim_parameters.prey_trajectory_radius_mm.value
        self.program['u_prey_capture_type'] = self.shared_stim_parameters.prey_capture_type
        self.program['u_n_preys'] = self.shared_stim_parameters.n_preys.value
        self.program['u_ramp_duration_sec'] = self.shared_stim_parameters.ramp_duration_sec.value
        self.program['u_ramp_powerlaw_exponent'] = self.shared_stim_parameters.ramp_powerlaw_exponent.value
        self.program['u_ramp_type'] = self.shared_stim_parameters.ramp_type.value

        if self._last_image_path != self.shared_stim_parameters.image_path.value:
            img_bgr = cv2.imread(self.shared_stim_parameters.image_path.value)
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            self.program['u_image_texture'] = img_rgb
            self.program['u_image_size'] = [img_rgb.shape[1], img_rgb.shape[0]]
            self._last_image_path = self.shared_stim_parameters.image_path.value

        self.program['u_image_res_px_per_mm'] = self.shared_stim_parameters.image_res_px_per_mm.value
        self.program['u_image_offset_mm'] = self.shared_stim_parameters.image_offset_mm[:]


    def initialize(self):
        # this runs in the display process

        super().initialize()
        
        # init shader
        np.random.seed(0)
        x = np.random.randint(0, self.camera_resolution[0], MAX_PREY)
        y = np.random.randint(0, self.camera_resolution[1], MAX_PREY)
        theta = np.random.uniform(0, 2*np.pi, (MAX_PREY,1))
        self.program['u_n_animals'] = self.n_animals
        self.program['u_prey_position'] = self.transformation_matrix.transform_points(np.column_stack((x, y)).astype(np.float32)).squeeze()
        self.program['u_prey_trajectory_angle'] = theta.astype(np.float32)

        self.show()
        self.timer = app.Timer(1/self.refresh_rate, self.on_timer)
        self.timer.start()

        self.initialized.set()

    def cleanup(self):
        super().cleanup()

    def on_draw(self, event):
        super().on_draw(event)
        gloo.clear('black')
        self.program.draw('triangle_strip')

    def on_timer(self, event):
        # this runs in the display process

        timestamp = get_time_ns()
        timestamp_sec = 1e-9*timestamp
        time_sec = timestamp_sec % self.rollover_time_sec

        self.update_shader_variables(time_sec)

        # log stim parameters on change as close as possible to hardware
        if self.stim_change_counter != self.shared_stim_parameters.stim_change_counter.value:
            stim_log = self.shared_stim_parameters.to_dict()
            if self.log_queue is not None:
                self.log_queue.put(stim_log)
            self.stim_change_counter = self.shared_stim_parameters.stim_change_counter.value

        self.update()

    def process_data(self, data) -> None:
        # this runs in the worker process

        # TODO use get instead of try except ?
        if data is None:
            return
        
        try:
            if not data['tracking']['success']:
                return
            
            fields = data['tracking'].dtype.names
            ID = data['identity']

            if 'body' in fields and data['tracking']['body']['success']:
                self.shared_fish_state[ID].fish_centroid[:] = self.transformation_matrix.transform_points(data['tracking']['body']['centroid_global']).squeeze()
                body_axes = data['tracking']['body']['body_axes_global']                
                self.shared_fish_state[ID].fish_caudorostral_axis[:] = self.transformation_matrix.transform_vectors(body_axes[:,0]).squeeze()
                self.shared_fish_state[ID].fish_mediolateral_axis[:] = self.transformation_matrix.transform_vectors(body_axes[:,1]).squeeze()
            else:
                self.shared_fish_state[ID].fish_centroid[:] =  self.transformation_matrix.transform_points(data['tracking']['animals']['centroids_global']).squeeze()

            # TODO use eyes heading vector if present?
            # eyes
            if 'eyes' in fields and data['tracking']['eyes']['success']:

                if data['tracking']['eyes']['left_eye'] is not None:
                    self.shared_fish_state[ID].left_eye_centroid[:] = self.transformation_matrix.transform_points(data['tracking']['eyes']['left_eye']['centroid_cropped']).squeeze()
                    self.shared_fish_state[ID].left_eye_angle.value = data['tracking']['eyes']['left_eye']['angle']

                if data['tracking']['eyes']['right_eye'] is not None:
                    self.shared_fish_state[ID].right_eye_centroid[:] =  self.transformation_matrix.transform_points(data['tracking']['eyes']['right_eye']['centroid_cropped']).squeeze()
                    self.shared_fish_state[ID].right_eye_angle.value = data['tracking']['eyes']['right_eye']['angle']

            # tail
            if 'tail' in fields and data['tracking']['tail']['success']:
                skeleton_interp = self.transformation_matrix.transform_points(data['tracking']['tail']['skeleton_interp_cropped'])
                self.shared_fish_state[ID].tail_points[:self.num_tail_points_interp] = skeleton_interp[:,0]
                self.shared_fish_state[ID].tail_points[self.num_tail_points_interp:] = skeleton_interp[:,1]

        except KeyError as err:
            print(f'KeyError: {err}')
            return None 
        
        except TypeError as err:
            print(f'TypeError: {err}')
            return None
        
        except ValueError as err:
            print(f'ValueError: {err}')
            return None

    def process_metadata(self, metadata):
        # this runs in the worker process

        log_message = None
        try:
            if self.log_queue is not None:
                log_message = self.log_queue.get_nowait()
        except queue.Empty:
            pass
        
        control: Dict = metadata['stim_control']  
        if control is None:
            return log_message
        
        if control.get('stim_select') in VISUAL_STIMS:
            timestamp = get_time_ns()
            timestamp_sec = 1e-9*timestamp
            time_sec = timestamp_sec % self.rollover_time_sec
            control['time_sec'] = time_sec
            self.shared_stim_parameters.from_dict(control)

        return log_message