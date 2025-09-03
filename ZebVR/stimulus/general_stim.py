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
        
        self.stim_change_counter = RawValue('d', 0) 
        self.start_time_sec = RawValue('d', 0) 
        self.stim_select = RawValue('d', Stim.DARK) 
        self.foreground_color = RawArray('d', DEFAULT['foreground_color'])
        self.background_color = RawArray('d', DEFAULT['background_color'])
        self.phototaxis_polarity = RawValue('d', DEFAULT['phototaxis_polarity']) 
        self.omr_spatial_period_mm = RawValue('d', DEFAULT['omr_spatial_period_mm'])
        self.omr_angle_deg = RawValue('d', DEFAULT['omr_angle_deg'])
        self.omr_speed_mm_per_sec = RawValue('d', DEFAULT['omr_speed_mm_per_sec'])
        self.concentric_spatial_period_mm = RawValue('d', DEFAULT['concentric_spatial_period_mm'])
        self.concentric_speed_mm_per_sec = RawValue('d', DEFAULT['concentric_speed_mm_per_sec'])
        self.okr_spatial_frequency_deg = RawValue('d', DEFAULT['okr_spatial_frequency_deg'])
        self.okr_speed_deg_per_sec = RawValue('d', DEFAULT['okr_speed_deg_per_sec'])
        self.looming_center_mm = RawArray('d', DEFAULT['looming_center_mm'])
        self.looming_period_sec = RawValue('d', DEFAULT['looming_period_sec'])
        self.looming_expansion_time_sec = RawValue('d', DEFAULT['looming_expansion_time_sec'])
        self.looming_expansion_speed_mm_per_sec = RawValue('d', DEFAULT['looming_expansion_speed_mm_per_sec'])
        self.dot_center_mm = RawArray('d', DEFAULT['dot_center_mm'])
        self.dot_radius_mm = RawValue('d', DEFAULT['dot_radius_mm'])
        self.n_preys = RawValue('L', DEFAULT['n_preys'])
        self.prey_speed_mm_s = RawValue('d', DEFAULT['prey_speed_mm_s'])
        self.prey_radius_mm = RawValue('d', DEFAULT['prey_radius_mm'])
        self.image_path = SharedString(initializer = DEFAULT['image_path'])
        self.image_res_px_per_mm = RawValue('d', DEFAULT['image_res_px_per_mm'])
        self.image_offset_mm = RawArray('d', DEFAULT['image_offset_mm'])
        self.ramp_duration_sec = RawValue('d', DEFAULT['ramp_duration_sec'])
        self.ramp_powerlaw_exponent = RawValue('d', DEFAULT['ramp_powerlaw_exponent'])
        self.ramp_type = RawValue('d', DEFAULT['ramp_type'])

    def from_dict(self, d: Dict) -> None:
        
        self.stim_change_counter.value += 1 # TODO filter on VISUAL STIM only 
        self.start_time_sec.value = d.get('time_sec', 0)
        self.stim_select.value = d.get('stim_select', Stim.DARK)
        self.foreground_color[:] = d.get('foreground_color', DEFAULT['foreground_color'])
        self.background_color[:] = d.get('background_color', DEFAULT['background_color'])
        self.phototaxis_polarity.value = d.get('phototaxis_polarity', DEFAULT['phototaxis_polarity'])
        self.omr_spatial_period_mm.value = d.get('omr_spatial_period_mm', DEFAULT['omr_spatial_period_mm'])
        self.omr_angle_deg.value = d.get('omr_angle_deg', DEFAULT['omr_angle_deg'])
        self.omr_speed_mm_per_sec.value = d.get('omr_speed_mm_per_sec', DEFAULT['omr_speed_mm_per_sec'])
        self.concentric_spatial_period_mm.value = d.get('concentric_spatial_period_mm', DEFAULT['concentric_spatial_period_mm'])
        self.concentric_speed_mm_per_sec.value = d.get('concentric_speed_mm_per_sec', DEFAULT['concentric_speed_mm_per_sec'])
        self.okr_spatial_frequency_deg.value = d.get('okr_spatial_frequency_deg', DEFAULT['okr_spatial_frequency_deg'])
        self.okr_speed_deg_per_sec.value = d.get('okr_speed_deg_per_sec', DEFAULT['okr_speed_deg_per_sec'])
        self.looming_center_mm[:] = d.get('looming_center_mm', DEFAULT['looming_center_mm'])
        self.looming_period_sec.value = d.get('looming_period_sec', DEFAULT['looming_period_sec'])
        self.looming_expansion_time_sec.value = d.get('looming_expansion_time_sec', DEFAULT['looming_expansion_time_sec'])
        self.looming_expansion_speed_mm_per_sec.value = d.get('looming_expansion_speed_mm_per_sec', DEFAULT['looming_expansion_speed_mm_per_sec'])
        self.dot_center_mm[:] = d.get('dot_center_mm', DEFAULT['dot_center_mm'])
        self.dot_radius_mm.value = d.get('dot_radius_mm', DEFAULT['dot_radius_mm'])
        self.n_preys.value = int(d.get('n_preys', DEFAULT['n_preys']))
        self.prey_speed_mm_s.value = d.get('prey_speed_mm_s', DEFAULT['prey_speed_mm_s'])
        self.prey_radius_mm.value = d.get('prey_radius_mm', DEFAULT['prey_radius_mm'])
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

        if self.stim_select.value in [Stim.LOOMING, Stim.FOLLOWING_LOOMING]:
            res.update({
                'looming_center_mm': list(self.looming_center_mm),
                'looming_period_sec': self.looming_period_sec.value,
                'looming_expansion_time_sec': self.looming_expansion_time_sec.value,
                'looming_expansion_speed_mm_per_sec': self.looming_expansion_speed_mm_per_sec.value,
            })

        if self.stim_select.value in [Stim.DOT, Stim.FOLLOWING_DOT]:
            res.update({
                'dot_center_mm': list(self.dot_center_mm),
                'dot_radius_mm': self.dot_radius_mm.value,
            })

        if self.stim_select.value == Stim.PREY_CAPTURE:
            res.update({
                'n_preys': self.n_preys.value,
                'prey_speed_mm_s': self.prey_speed_mm_s.value,
                'prey_radius_mm': self.prey_radius_mm.value,
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
            init_centroid: Tuple[float, float] = (0.0, 0.0),
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

        // tracking
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
        uniform float u_stim_select;
        uniform float u_phototaxis_polarity;
        uniform float u_omr_spatial_period_mm;
        uniform float u_omr_angle_deg;
        uniform float u_omr_speed_mm_per_sec;
        uniform float u_concentric_spatial_period_mm;
        uniform float u_concentric_speed_mm_per_sec;
        uniform float u_okr_spatial_frequency_deg;
        uniform float u_okr_speed_deg_per_sec;
        uniform vec2 u_looming_center_mm;
        uniform float u_looming_period_sec;
        uniform float u_looming_expansion_time_sec;
        uniform float u_looming_expansion_speed_mm_per_sec;
        uniform vec2 u_dot_center_mm;
        uniform float u_dot_radius_mm;
        uniform float u_n_preys;
        uniform float u_prey_radius_mm;
        uniform float u_prey_speed_mm_s;
        uniform vec2 u_prey_position[{MAX_PREY}];
        uniform vec2 u_prey_direction[{MAX_PREY}];
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
        
        const int DARK = 0;
        const int BRIGHT = 1;
        const int PHOTOTAXIS = 2;
        const int OMR = 3;
        const int OKR = 4;
        const int FOLLOWING_LOOMING = 5;
        const int PREY_CAPTURE = 6;
        const int LOOMING = 7;
        const int CONCENTRIC_GRATING = 8;
        const int FOLLOWING_DOT = 9;
        const int DOT = 10;
        const int IMAGE = 11;
        const int RAMP = 12;

        const float PI = radians(180.0);
        const float EPS = 1e-6;

        """ + """

        // helper functions
        bool is_point_in_bbox(vec2 point, vec2 minBounds, vec2 maxBounds) {
            return all(greaterThanEqual(point, minBounds)) && all(lessThanEqual(point, maxBounds));
        }

        mat2 rotate2d(float angle_rad){
            return mat2(cos(angle_rad),-sin(angle_rad),
                        sin(angle_rad),cos(angle_rad));
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

        void main()
        {
            vec2 coordinates_centered_px;
            mat2 change_of_basis;
            vec2 fish_ego_coords_px;
            vec2 fish_ego_coords_mm;
            vec4 camera_bbox_px;
            vec4 camera_bbox_mm;

            vec2 coordinates_px = gl_FragCoord.xy * u_pixel_scaling;
            vec2 coordinates_mm = coordinates_px / u_pix_per_mm_proj;
            vec3 camera_coordinates_px = u_proj_to_cam * vec3(coordinates_px, 1.0);
            vec2 camera_coordinates_mm = camera_coordinates_px.xy / u_pix_per_mm;

            gl_FragColor = vec4(0,0,0,1);

            for (int animal = 0; animal < u_n_animals; animal++) {

                camera_bbox_px = u_bounding_box[animal];
                if ( !is_point_in_bbox(camera_coordinates_px.xy, camera_bbox_px.xy, camera_bbox_px.xy+camera_bbox_px.wz) ) {
                    continue;
                }

                gl_FragColor = u_background_color; 

                vec3 proj_bbox_origin = u_cam_to_proj * vec3(camera_bbox_px.xy, 1.0);
                vec3 proj_bbox_size = u_cam_to_proj * vec3(camera_bbox_px.wz, 0.0);
                vec4 proj_bbox_px = vec4(proj_bbox_origin.xy, proj_bbox_size.xy);
                vec4 proj_bbox_mm = vec4(proj_bbox_origin.xy / u_pix_per_mm_proj, proj_bbox_size.xy/ u_pix_per_mm_proj);
                
                // compute pixel coordinates in fish egocentric coordinates (mm)
                coordinates_centered_px = coordinates_px - u_fish_centroid[animal];
                change_of_basis = mat2(
                    u_fish_mediolateral_axis[animal]/length(u_fish_mediolateral_axis[animal]), 
                    u_fish_caudorostral_axis[animal]/length(u_fish_caudorostral_axis[animal])
                );
                fish_ego_coords_px = transpose(change_of_basis) * coordinates_centered_px;
                fish_ego_coords_mm = fish_ego_coords_px / u_pix_per_mm_proj;
                
                // implement the different stimuli
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
                    vec2 orientation_vector = rotate2d(radians(u_omr_angle_deg)) * vec2(0,1);
                    float position_on_orientation_vector = dot(fish_ego_coords_mm, orientation_vector)/length(orientation_vector);
                    float spatial_freq = 1/u_omr_spatial_period_mm;
                    float temporal_freq = u_omr_speed_mm_per_sec/u_omr_spatial_period_mm;
                    float angle = spatial_freq * position_on_orientation_vector;
                    float phase = temporal_freq * u_time_s;

                    if ( sin(2*PI*(angle+phase)) > 0.0 ) {
                        gl_FragColor = u_foreground_color;
                    } 
                }

                if (u_stim_select == OKR) {
                    float angular_spatial_freq = radians(u_okr_spatial_frequency_deg);
                    float angular_temporal_freq = radians(u_okr_speed_deg_per_sec);
                    
                    float angle = atan(fish_ego_coords_mm.y, fish_ego_coords_mm.x);
                    float phase = angular_temporal_freq * u_time_s;
                    if ( mod(angle+phase, angular_spatial_freq) > angular_spatial_freq/2 ) {
                        gl_FragColor = u_foreground_color;
                    } 
                }

                if (u_stim_select == DOT) {
                    if ( distance(coordinates_mm, proj_bbox_mm.xy + proj_bbox_mm.wz/2.0 + u_dot_center_mm) <= u_dot_radius_mm)
                    {
                        gl_FragColor = u_foreground_color;
                    }
                } 

                if (u_stim_select == FOLLOWING_DOT) {
                    if ( distance(fish_ego_coords_mm, u_dot_center_mm) <= u_dot_radius_mm)
                    {
                        gl_FragColor = u_foreground_color;
                    }
                } 

                if (u_stim_select == LOOMING) {
                    float rel_time = mod(u_time_s-u_start_time_s, u_looming_period_sec); 
                    float looming_on = float(rel_time<=u_looming_expansion_time_sec);
                    if ( distance(coordinates_mm, proj_bbox_mm.xy + proj_bbox_mm.wz/2.0 + u_looming_center_mm) <= u_looming_expansion_speed_mm_per_sec*rel_time*looming_on )
                    {
                        gl_FragColor = u_foreground_color;
                    }
                }

                if (u_stim_select == FOLLOWING_LOOMING) {
                    float rel_time = mod(u_time_s-u_start_time_s, u_looming_period_sec); 
                    float looming_on = float(rel_time<=u_looming_expansion_time_sec);
                    if ( distance(fish_ego_coords_mm, u_looming_center_mm) <= u_looming_expansion_speed_mm_per_sec*rel_time*looming_on )
                    {
                        gl_FragColor = u_foreground_color;
                    }
                } 

                if (u_stim_select == CONCENTRIC_GRATING) {
                    float distance_to_center_mm = distance(coordinates_mm, proj_bbox_mm.xy + proj_bbox_mm.wz/2.0);
                    float spatial_freq = 1/u_concentric_spatial_period_mm;
                    float temporal_freq = u_concentric_speed_mm_per_sec/u_concentric_spatial_period_mm;
                    float angle = spatial_freq * distance_to_center_mm;
                    float phase = temporal_freq * u_time_s;
                    if ( sin(2*PI*(angle+phase)) > 0.0 ) 
                    {
                        gl_FragColor = u_foreground_color;
                    }
                }

                if (u_stim_select == PREY_CAPTURE) {
                    for (int i = 0; i < u_n_preys; i++) {
                        vec2 pos_camera_px =  camera_bbox_px.xy + mod(u_prey_position[i] + u_time_s * u_prey_speed_mm_s * u_pix_per_mm * u_prey_direction[i], camera_bbox_px.wz);
                        vec3 pos_proj_px = u_cam_to_proj * vec3(pos_camera_px, 1.0);
                        if ( distance(pos_proj_px.xy/u_pix_per_mm_proj, coordinates_mm) <= u_prey_radius_mm ) {
                            gl_FragColor = u_foreground_color;
                        }
                    }
                }

                if (u_stim_select == IMAGE) {
                    vec2 image_size_mm = u_image_size / u_image_res_px_per_mm;
                    vec2 coords = (coordinates_mm - u_image_offset_mm - proj_bbox_mm.xy) / image_size_mm;
                    if (coords.x >= 0.0 && coords.x <= 1.0 &&
                        coords.y >= 0.0 && coords.y <= 1.0) {
                        gl_FragColor = texture2D(u_image_texture, coords);
                    }
                }

                if (u_stim_select == RAMP) {
                    float t = mod(u_time_s-u_start_time_s, u_ramp_duration_sec);
                    float frac = clamp(t / u_ramp_duration_sec, 0.0, 1.0);
                    float ramp_value = 0.0;

                    if (u_ramp_type == LINEAR) {
                        ramp_value = frac;
                    }

                    if (u_ramp_type == POWER_LAW) {
                        // Stevens' law: S = kI**a 
                        float exponent = u_ramp_powerlaw_exponent;
                        ramp_value = pow(frac, 1/exponent);
                    }

                    vec4 color = mix(u_background_color, u_foreground_color, ramp_value);
                    gl_FragColor = color;
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
        for fish_state in self.shared_fish_state:
            fish_state.fish_caudorostral_axis[:] = init_heading[:,0]
            fish_state.fish_mediolateral_axis[:] = init_heading[:,1]
            fish_state.fish_centroid[:] = init_centroid

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
        self.program['u_stim_select'] = self.shared_stim_parameters.stim_select.value
        self.program['u_phototaxis_polarity'] = self.shared_stim_parameters.phototaxis_polarity.value
        self.program['u_omr_spatial_period_mm'] = self.shared_stim_parameters.omr_spatial_period_mm.value
        self.program['u_omr_angle_deg'] = self.shared_stim_parameters.omr_angle_deg.value
        self.program['u_omr_speed_mm_per_sec'] = self.shared_stim_parameters.omr_speed_mm_per_sec.value
        self.program['u_concentric_spatial_period_mm'] = self.shared_stim_parameters.concentric_spatial_period_mm.value
        self.program['u_concentric_speed_mm_per_sec'] = self.shared_stim_parameters.concentric_speed_mm_per_sec.value
        self.program['u_okr_spatial_frequency_deg'] = self.shared_stim_parameters.okr_spatial_frequency_deg.value
        self.program['u_okr_speed_deg_per_sec'] = self.shared_stim_parameters.okr_speed_deg_per_sec.value
        self.program['u_looming_center_mm'] = self.shared_stim_parameters.looming_center_mm[:]
        self.program['u_looming_period_sec'] = self.shared_stim_parameters.looming_period_sec.value
        self.program['u_looming_expansion_time_sec'] = self.shared_stim_parameters.looming_expansion_time_sec.value
        self.program['u_looming_expansion_speed_mm_per_sec'] = self.shared_stim_parameters.looming_expansion_speed_mm_per_sec.value
        self.program['u_dot_center_mm'] = self.shared_stim_parameters.dot_center_mm[:]
        self.program['u_dot_radius_mm'] = self.shared_stim_parameters.dot_radius_mm.value
        self.program['u_prey_speed_mm_s'] = self.shared_stim_parameters.prey_speed_mm_s.value
        self.program['u_prey_radius_mm'] = self.shared_stim_parameters.prey_radius_mm.value
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
        theta = np.random.uniform(0, 2*np.pi, MAX_PREY)
        self.program['u_n_animals'] = self.n_animals
        self.program['u_prey_position'] = np.column_stack((x, y)).astype(np.float32)
        self.program['u_prey_direction'] = np.column_stack((np.cos(theta), np.sin(theta))).astype(np.float32)
        self.update_shader_variables(0)

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