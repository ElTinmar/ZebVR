from typing import Tuple
from .visual_stim import VisualStim
from vispy import gloo, app
from multiprocessing import RawValue, RawArray
import time
from numpy.typing import NDArray
import numpy as np 
import os

# TODO adapt shader code to receive state from all animals and display only in their respective ROIs.
# TODO pass state of all animals to the shader (multidim RawArray)
# TODO maybe pass ROIs to __init__ instead of sending for each frame along with tracking data

VERT_SHADER = """
uniform mat3 u_transformation_matrix;
uniform float u_pix_per_mm; 
attribute vec2 a_position;

// tracking
attribute vec2 a_fish_caudorostral_axis;
attribute vec2 a_fish_mediolateral_axis;
attribute vec2 a_fish_centroid; 
attribute vec2 a_left_eye_centroid; 
attribute float a_left_eye_angle;
attribute vec2 a_right_eye_centroid;
attribute float a_right_eye_angle;

varying vec2 v_fish_caudorostral_axis;
varying vec2 v_fish_mediolateral_axis;
varying vec2 v_fish_centroid;
varying vec2 v_left_eye_centroid; 
varying float v_left_eye_angle;
varying vec2 v_right_eye_centroid;
varying float v_right_eye_angle;
varying vec2 v_pix_per_mm_proj;

void main()
{
    gl_Position = vec4(a_position, 0.0, 1.0);

    //NOTE setting last component to 0 for scaling without translation
    vec3 fish_centroid = u_transformation_matrix * vec3(a_fish_centroid, 1.0);
    vec3 left_eye_centroid = u_transformation_matrix * vec3(a_left_eye_centroid, 1.0);
    vec3 right_eye_centroid = u_transformation_matrix * vec3(a_right_eye_centroid, 1.0);
    vec3 fish_caudorostral_axis = u_transformation_matrix * vec3(a_fish_caudorostral_axis, 0);
    vec3 fish_mediolateral_axis = u_transformation_matrix * vec3(a_fish_mediolateral_axis, 0);
    vec3 proj_scale = u_transformation_matrix * vec3(u_pix_per_mm, u_pix_per_mm, 0);

    v_fish_centroid = fish_centroid.xy;
    v_left_eye_centroid = left_eye_centroid.xy;
    v_right_eye_centroid = right_eye_centroid.xy;
    v_fish_caudorostral_axis = fish_caudorostral_axis.xy;
    v_fish_mediolateral_axis = fish_mediolateral_axis.xy;
    v_left_eye_angle = a_left_eye_angle;
    v_right_eye_angle = a_right_eye_angle;
    v_pix_per_mm_proj = abs(proj_scale.xy);
} 
"""

MAX_PREY = 100

FRAG_SHADER = f"""
uniform vec2 u_prey_position[{MAX_PREY}];
uniform vec2 u_prey_direction[{MAX_PREY}];
""" + """
// Some DMD projectors with diamond pixel layouts (e.g. Lightcrafters) do not have uniform pixel spacing.
uniform vec2 u_pixel_scaling; 
uniform float u_pix_per_mm; 
varying vec2 v_pix_per_mm_proj;
uniform vec2 u_proj_resolution;
uniform vec2 u_cam_resolution;
uniform mat3 u_transformation_matrix;

// tracking
varying vec2 v_fish_centroid;
varying vec2 v_fish_caudorostral_axis;
varying vec2 v_fish_mediolateral_axis;
varying vec2 v_left_eye_centroid; 
varying float v_left_eye_angle;
varying vec2 v_right_eye_centroid;
varying float v_right_eye_angle;
uniform float u_time_s;

// stim parameters
uniform vec4 u_foreground_color;
uniform vec4 u_background_color;
uniform float u_stim_select;
uniform float u_phototaxis_polarity;
uniform float u_omr_spatial_period_mm;
uniform float u_omr_angle_deg;
uniform float u_omr_speed_mm_per_sec;
uniform float u_okr_spatial_frequency_deg;
uniform float u_okr_speed_deg_per_sec;
uniform vec2 u_looming_center_mm;
uniform float u_looming_period_sec;
uniform float u_looming_expansion_time_sec;
uniform float u_looming_expansion_speed_mm_per_sec;
uniform float u_n_preys;
uniform float u_prey_radius_mm;
uniform float u_prey_speed_mm_s;

// constants 
const int DARK = 0;
const int BRIGHT = 1;
const int PHOTOTAXIS = 2;
const int OMR = 3;
const int OKR = 4;
const int LOOMING = 5;
const int PREY_CAPTURE = 6;
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
    vec2 coordinates_px = gl_FragCoord.xy * u_pixel_scaling;
    vec2 coordinates_centered_px = coordinates_px - v_fish_centroid;
    vec2 coordinates_centered_mm = 1/v_pix_per_mm_proj * coordinates_centered_px;
    // X: mediolateral_axis, Y: caudorostral_axis
    mat2 change_of_basis = mat2(
        v_fish_mediolateral_axis/length(v_fish_mediolateral_axis), 
        v_fish_caudorostral_axis/length(v_fish_caudorostral_axis)
    );
    vec2 fish_ego_coords_mm = transpose(change_of_basis)*coordinates_centered_mm;
    
    gl_FragColor = u_background_color;

    if (u_stim_select == DARK) {
        gl_FragColor = u_background_color;
    }

    if (u_stim_select == BRIGHT) {
        gl_FragColor = u_foreground_color;
    }

    if (u_stim_select == PHOTOTAXIS) {
        if ( u_phototaxis_polarity * fish_ego_coords_mm.x > 0.0 ) {
            gl_FragColor = u_foreground_color;
        } 
    }

    if (u_stim_select == OMR) {
        vec2 orientation_vector = rotate2d(deg2rad(u_omr_angle_deg)) * vec2(0,1);
        float angle = 2*PI/u_omr_spatial_period_mm * dot(fish_ego_coords_mm, orientation_vector);
        float phase = 2*PI/u_omr_spatial_period_mm * u_omr_speed_mm_per_sec * u_time_s;
        if ( sin(angle+phase) > 0.0 ) {
            gl_FragColor = u_foreground_color;
        } 
    }

    if (u_stim_select == OKR) {
        float freq = deg2rad(u_okr_spatial_frequency_deg);
        float angle = atan(fish_ego_coords_mm.y, fish_ego_coords_mm.x);
        float phase = deg2rad(u_okr_speed_deg_per_sec)*u_time_s;
        if ( mod(angle+phase, freq) > freq/2 ) {
            gl_FragColor = u_foreground_color;
        } 
    }

    if (u_stim_select == LOOMING) {
        float rel_time = mod(u_time_s, u_looming_period_sec); 
        float looming_on = float(rel_time<=u_looming_expansion_time_sec);
        if ( rel_time <= u_looming_period_sec/2 ) { 
            if ( distance(fish_ego_coords_mm, u_looming_center_mm) <= u_looming_expansion_speed_mm_per_sec*rel_time*looming_on )
            {
                gl_FragColor = u_foreground_color;
            }
        }
    } 

    if (u_stim_select == PREY_CAPTURE) {
        for (int i = 0; i < u_n_preys; i++) {
            vec2 pos_camera_px = mod(u_prey_position[i] + u_time_s * u_prey_speed_mm_s * u_pix_per_mm * u_prey_direction[i], u_cam_resolution);
            vec3 pos_proj_px = u_transformation_matrix * vec3(pos_camera_px, 1.0);
            if ( distance(pos_proj_px.xy/v_pix_per_mm_proj, coordinates_px/v_pix_per_mm_proj) <= u_prey_radius_mm ) {
                gl_FragColor = u_foreground_color;
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
            camera_resolution: Tuple[int, int],
            foreground_color: Tuple[float, float, float, float] = (1.0, 0.0, 0.0, 1.0),
            background_color: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 1.0),
            window_decoration: bool = True,
            transformation_matrix: NDArray = np.eye(3, dtype=np.float32),
            pixel_scaling: Tuple[float, float] = (1.0,1.0),
            pix_per_mm: float = 30,
            refresh_rate: int = 120,
            vsync: bool = True,
            timings_file: str = 'stim.csv',
            num_tail_points_interp: int = 40,
            stim_select: float = 0,
            phototaxis_polarity: int = 1,
            omr_spatial_period_mm: float = 20,
            omr_angle_deg: float = 0,
            omr_speed_mm_per_sec: float = 360,
            okr_spatial_frequency_deg: float = 45,
            okr_speed_deg_per_sec: float = 60,
            looming_center_mm: Tuple = (1,1),
            looming_period_sec: float = 30,
            looming_expansion_time_sec: float = 3,
            looming_expansion_speed_mm_per_sec: float = 10,
            n_preys: int = 50,
            prey_speed_mm_s: float = 20, # 0.75
            prey_radius_mm: float = 50, # 0.25
        ) -> None:

        super().__init__(
            vertex_shader=VERT_SHADER, 
            fragment_shader=FRAG_SHADER, 
            window_size=window_size,
            window_position=window_position, 
            camera_resolution=camera_resolution,
            pix_per_mm=pix_per_mm, 
            window_decoration=window_decoration, 
            transformation_matrix=transformation_matrix, 
            pixel_scaling=pixel_scaling, 
            vsync=vsync
        )

        self.default_stim_select = stim_select
        self.default_background_color = background_color
        self.default_foreground_color = foreground_color
        self.default_phototaxis_polarity = phototaxis_polarity
        self.default_omr_spatial_period_mm = omr_spatial_period_mm
        self.default_omr_angle_deg = omr_angle_deg
        self.default_omr_speed_mm_per_sec = omr_speed_mm_per_sec
        self.default_okr_spatial_frequency_deg = okr_spatial_frequency_deg
        self.default_okr_speed_deg_per_sec = okr_speed_deg_per_sec 
        self.default_looming_center_mm = looming_center_mm
        self.default_looming_period_sec = looming_period_sec
        self.default_looming_expansion_time_sec = looming_expansion_time_sec
        self.default_looming_expansion_speed_mm_per_sec = looming_expansion_speed_mm_per_sec
        self.default_n_prey = n_preys
        self.default_prey_speed_mm_s = prey_speed_mm_s
        self.default_prey_radius_mm = prey_radius_mm 
        self.num_tail_points_interp = num_tail_points_interp

        self.tail_points = RawArray('d', 2*self.num_tail_points_interp)
        self.foreground_color = RawArray('d', self.default_foreground_color)
        self.background_color = RawArray('d', self.default_background_color)
        self.stim_select = RawValue('d', self.default_stim_select) 
        self.phototaxis_polarity = RawValue('d', self.default_phototaxis_polarity) 
        self.omr_spatial_period_mm = RawValue('d', self.default_omr_spatial_period_mm)
        self.omr_angle_deg = RawValue('d', self.default_omr_angle_deg)
        self.omr_speed_mm_per_sec = RawValue('d', self.default_omr_speed_mm_per_sec)
        self.okr_spatial_frequency_deg = RawValue('d', self.default_okr_spatial_frequency_deg)
        self.okr_speed_deg_per_sec = RawValue('d', self.default_okr_speed_deg_per_sec)
        self.looming_center_mm = RawArray('d', self.default_looming_center_mm)
        self.looming_period_sec = RawValue('d', self.default_looming_period_sec)
        self.looming_expansion_time_sec = RawValue('d', self.default_looming_expansion_time_sec)
        self.looming_expansion_speed_mm_per_sec = RawValue('d', self.default_looming_expansion_speed_mm_per_sec)
        self.n_preys = RawValue('L', self.default_n_prey)
        self.prey_speed_mm_s = RawValue('d', self.default_prey_speed_mm_s)
        self.prey_radius_mm = RawValue('d', self.default_prey_radius_mm)

        self.index = RawValue('L', 0)
        self.timestamp = RawValue('d', 0)
        self.identity = RawValue('L', 0)
        self.fish_mediolateral_axis = RawArray('d', [0, 0])
        self.fish_caudorostral_axis = RawArray('d', [0, 0])
        self.fish_centroid = RawArray('d', [0, 0])
        self.left_eye_centroid = RawArray('d', [0, 0])
        self.left_eye_angle = RawValue('d', 0)
        self.right_eye_centroid = RawArray('d', [0, 0])
        self.right_eye_angle = RawValue('d', 0)

        self.refresh_rate = refresh_rate
        self.fd = None
        self.tstart = 0
        self.timings_file = timings_file

    def set_filename(self, filename:str):
        self.timings_file = filename

    def initialize_shared_variables(self):

        self.foreground_color[:] = self.default_foreground_color
        self.background_color[:] = self.default_background_color
        self.stim_select.value = self.default_stim_select
        self.phototaxis_polarity.value = self.default_phototaxis_polarity 
        self.omr_spatial_period_mm.value = self.default_omr_spatial_period_mm
        self.omr_angle_deg.value = self.default_omr_angle_deg
        self.omr_speed_mm_per_sec.value = self.default_omr_speed_mm_per_sec
        self.okr_spatial_frequency_deg.value = self.default_okr_spatial_frequency_deg
        self.okr_speed_deg_per_sec.value = self.default_okr_speed_deg_per_sec
        self.looming_center_mm[:] = self.default_looming_center_mm
        self.looming_period_sec.value = self.default_looming_period_sec
        self.looming_expansion_time_sec.value = self.default_looming_expansion_time_sec
        self.looming_expansion_speed_mm_per_sec.value = self.default_looming_expansion_speed_mm_per_sec
        self.n_preys.value = self.default_n_prey
        self.prey_speed_mm_s.value = self.default_prey_speed_mm_s
        self.prey_radius_mm.value = self.default_prey_radius_mm

        self.index.value = 0
        self.timestamp.value = 0
        self.identity.value = 0
        self.fish_mediolateral_axis[:] = [0, 0]
        self.fish_caudorostral_axis[:] = [0, 0]
        self.fish_centroid[:] = [0, 0]
        self.left_eye_centroid[:] = [0, 0]
        self.left_eye_angle.value = 0
        self.right_eye_centroid[:] = [0, 0]
        self.right_eye_angle.value = 0

    def update_shader_variables(self, time: float):
        # communication between CPU and GPU for every frame drawn

        self.program['u_time_s'] = time
        self.program['a_fish_caudorostral_axis'] = self.fish_caudorostral_axis[:]
        self.program['a_fish_mediolateral_axis'] = self.fish_mediolateral_axis[:]
        self.program['a_left_eye_centroid'] = self.left_eye_centroid[:]
        self.program['a_left_eye_angle'] = self.left_eye_angle.value
        self.program['a_right_eye_centroid'] = self.right_eye_centroid[:]
        self.program['a_right_eye_angle'] = self.right_eye_angle.value
        self.program['a_fish_centroid'] = self.fish_centroid[:]
        self.program['u_foreground_color'] = self.foreground_color[:]
        self.program['u_background_color'] = self.background_color[:]
        self.program['u_stim_select'] = self.stim_select.value
        self.program['u_phototaxis_polarity'] = self.phototaxis_polarity.value
        self.program['u_omr_spatial_period_mm'] = self.omr_spatial_period_mm.value
        self.program['u_omr_angle_deg'] = self.omr_angle_deg.value
        self.program['u_omr_speed_mm_per_sec'] = self.omr_speed_mm_per_sec.value
        self.program['u_okr_spatial_frequency_deg'] = self.okr_spatial_frequency_deg.value
        self.program['u_okr_speed_deg_per_sec'] = self.okr_speed_deg_per_sec.value
        self.program['u_looming_center_mm'] = self.looming_center_mm[:]
        self.program['u_looming_period_sec'] = self.looming_period_sec.value
        self.program['u_looming_expansion_time_sec'] = self.looming_expansion_time_sec.value
        self.program['u_looming_expansion_speed_mm_per_sec'] = self.looming_expansion_speed_mm_per_sec.value
        self.program['u_prey_speed_mm_s'] = self.prey_speed_mm_s.value
        self.program['u_prey_radius_mm'] = self.prey_radius_mm.value
        self.program['u_n_preys'] = self.n_preys.value

    def initialize(self):

        super().initialize()

        self.initialize_shared_variables()
        
        np.random.seed(0)
        x = np.random.randint(0, self.camera_resolution[0], MAX_PREY)
        y = np.random.randint(0, self.camera_resolution[1], MAX_PREY)
        theta = np.random.uniform(0, 2*np.pi, MAX_PREY)
        self.program['u_prey_position'] = np.column_stack((x, y)).astype(np.float32)
        self.program['u_prey_direction'] = np.column_stack((np.cos(theta), np.sin(theta))).astype(np.float32)

        # init file name
        prefix, ext = os.path.splitext(self.timings_file)
        timings_file = prefix + time.strftime('_%a_%d_%b_%Y_%Hh%Mmin%Ssec') + ext
        while os.path.exists(timings_file):
            time.sleep(1)
            timings_file = prefix + time.strftime('_%a_%d_%b_%Y_%Hh%Mmin%Ssec') + ext

        # write csv headers
        self.fd = open(timings_file, 'w')
        headers = (
            'timestamp',
            'stim_id',
            'phototaxis_polarity',
            'omr_spatial_period_mm',
            'omr_angle_deg',
            'omr_speed_mm_per_sec',
            'okr_spatial_frequency_deg',
            'okr_speed_deg_per_sec',
            'looming_center_mm_x',
            'looming_center_mm_y',
            'looming_period_sec',
            'looming_expansion_time_sec',
            'looming_expansion_speed_mm_per_sec',
            'n_prey',
            'prey_speed_mm_s',
            'prey_radius_mm'
        )
        self.fd.write(','.join(headers) + '\n')
        
        # init shader
        self.update_shader_variables(0)

        self.show()
        self.timer = app.Timer(1/self.refresh_rate, self.on_timer)
        self.timer.start()

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
        
        timestamp = time.perf_counter_ns()

        self.update_shader_variables(timestamp)
        self.update()

        row = (
            f'{timestamp}',
            f'{self.stim_select.value}',
            f'{self.phototaxis_polarity.value}',
            f'{self.omr_spatial_period_mm.value}',
            f'{self.omr_angle_deg.value}',
            f'{self.omr_speed_mm_per_sec.value}',
            f'{self.okr_spatial_frequency_deg.value}',
            f'{self.okr_speed_deg_per_sec.value}',
            f'{self.looming_center_mm[0]}',
            f'{self.looming_center_mm[1]}',
            f'{self.looming_period_sec.value}',
            f'{self.looming_expansion_time_sec.value}',
            f'{self.looming_expansion_speed_mm_per_sec.value}',
            f'{self.n_preys.value}',
            f'{self.prey_speed_mm_s.value}',
            f'{self.prey_radius_mm.value}'
        )
        self.fd.write(','.join(row) + '\n')

    def process_data(self, data) -> None:

        if data is None:
            return

        try:
            self.index.value = data['index']
            self.timestamp.value = data['timestamp']
            self.identity.value = data['identity']

            #data['origin']
            #data['shape']

            print(f"frame {data['index']}, fish {data['identity']}: latency {1e-6*(time.perf_counter_ns() - data['timestamp'])}")
            
            # TODO maybe create a single fish tracker
            k = 0

            if data['tracking']['body'][k] is not None:
                self.fish_centroid[:] = data['tracking']['body'][k]['centroid_global']
                body_axes = data['tracking']['body'][k]['body_axes_global']
                self.fish_caudorostral_axis[:] = body_axes[:,0]
                self.fish_mediolateral_axis[:] = body_axes[:,1]
            else:
                self.fish_centroid[:] = data['tracking']['animals']['centroid_global'][k,:]

            # TODO use eyes heading vector if present?
            # eyes
            if data['tracking']['eyes'][k] is not None:

                if data['tracking']['eyes'][k]['left_eye'] is not None:
                    self.left_eye_centroid[:] = data['tracking']['eyes'][k]['left_eye']['centroid_cropped'] 
                    self.left_eye_angle.value = data['tracking']['eyes'][k]['left_eye']['angle']

                if data['tracking']['eyes'][k]['right_eye'] is not None:
                    self.right_eye_centroid[:] = data['tracking']['eyes'][k]['right_eye']['centroid_cropped']
                    self.right_eye_angle.value = data['tracking']['eyes'][k]['right_eye']['angle']

            # tail
            if data['tracking']['tail'][k] is not None:
                skeleton_interp = data['tracking']['tail'][k]['skeleton_interp_cropped']  
                self.tail_points[:self.num_tail_points_interp] = skeleton_interp[:,0]
                self.tail_points[self.num_tail_points_interp:] = skeleton_interp[:,1]

        except KeyError:
            return None 
        
        except TypeError:
            return None
        
        except ValueError:
            return None

    def process_metadata(self, metadata) -> None:

        control = metadata['visual_stim_control']
        
        if control is None:
            return
        
        self.stim_select.value = control['stim_select']
        self.phototaxis_polarity.value = control['phototaxis_polarity']
        self.omr_spatial_period_mm.value = control['omr_spatial_period_mm']
        self.omr_angle_deg.value = control['omr_angle_deg']
        self.omr_speed_mm_per_sec.value = control['omr_speed_mm_per_sec']
        self.okr_spatial_frequency_deg.value = control['okr_spatial_frequency_deg']
        self.okr_speed_deg_per_sec.value = control['okr_speed_deg_per_sec']
        self.looming_center_mm[:] = control['looming_center_mm']
        self.looming_period_sec.value = control['looming_period_sec']
        self.looming_expansion_time_sec.value = control['looming_expansion_time_sec']
        self.looming_expansion_speed_mm_per_sec.value = control['looming_expansion_speed_mm_per_sec']
        self.foreground_color[:] = control['foreground_color']
        self.background_color[:] = control['background_color']
        self.n_preys.value = int(control['n_preys'])
        self.prey_speed_mm_s.value = control['prey_speed_mm_s']
        self.prey_radius_mm.value = control['prey_radius_mm']