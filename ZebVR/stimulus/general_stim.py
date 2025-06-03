from typing import List, Tuple, Dict
from .visual_stim import VisualStim
from vispy import gloo, app
from multiprocessing import RawValue, RawArray
import time
import numpy as np 
import os
from dataclasses import dataclass
from geometry import AffineTransform2D
from ZebVR import MAX_PREY
from ZebVR.protocol import DEFAULT, Stim

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

# TODO maybe also make that an array per fish if you want each fish to receive a different stimulus
class SharedStimParameters:

    def __init__(self):
        
        self.start_time_sec = RawValue('d', 0) 
        self.stim_select = RawValue('d', Stim.Visual.DARK) 
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

    def from_dict(self, d: Dict) -> None:

        self.start_time_sec.value = d.get('time_sec', 0)
        self.stim_select.value = d.get('stim_select', Stim.Visual.DARK)
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
            transformation_matrix: AffineTransform2D = AffineTransform2D.identity(),
            pixel_scaling: Tuple[float, float] = (1.0,1.0),
            pix_per_mm: float = 30,
            refresh_rate: int = 120,
            vsync: bool = False,
            fullscreen: bool = True,
            timings_file: str = 'stim.csv',
            num_tail_points_interp: int = 40,
            rollover_time_sec: float = 3600 # TODO add that to a gui somewhere
        ) -> None:

        self.ROI_identities = ROI_identities
        self.num_tail_points_interp = num_tail_points_interp
        self.n_animals = len(ROI_identities)
        self.rollover_time_sec = rollover_time_sec

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

        // constants 
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
        const int BRIGHTNESS_RAMP = 12;

        const float PI = radians(180.0);

        """ + """

        // helper functions
        bool is_point_in_bbox(vec2 point, vec2 minBounds, vec2 maxBounds) {
            return all(greaterThanEqual(point, minBounds)) && all(lessThanEqual(point, maxBounds));
        }

        mat2 rotate2d(float angle_rad){
            return mat2(cos(angle_rad),-sin(angle_rad),
                        sin(angle_rad),cos(angle_rad));
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
        self.shared_stim_parameters = SharedStimParameters()

        self.refresh_rate = refresh_rate
        self.fd = None
        self.timings_file = timings_file
        self.tstart = 0

    def set_filename(self, filename:str):
        self.timings_file = filename

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

    def initialize(self):
        # this runs in the display process

        super().initialize()
        
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
            'time_sec',
            'stim_id',          
            'start_time_sec',
            'phototaxis_polarity',
            'omr_spatial_period_mm',
            'omr_angle_deg',
            'omr_speed_mm_per_sec',
            'concentric_spatial_period_mm',
            'concentric_speed_mm_per_sec',
            'okr_spatial_frequency_deg',
            'okr_speed_deg_per_sec',
            'looming_center_mm_x',
            'looming_center_mm_y',
            'looming_period_sec',
            'looming_expansion_time_sec',
            'looming_expansion_speed_mm_per_sec',
            'dot_center_mm_x',
            'dot_center_mm_y',
            'dot_radius_mm',
            'n_prey',
            'prey_speed_mm_s',
            'prey_radius_mm'
        )
        self.fd.write(','.join(headers) + '\n')
        
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
        self.fd.close()

    def on_draw(self, event):
        super().on_draw(event)
        gloo.clear('black')
        self.program.draw('triangle_strip')

    def on_timer(self, event):
        # this runs in the display process

        timestamp = time.perf_counter_ns()
        timestamp_sec = 1e-9*timestamp
        time_sec = timestamp_sec % self.rollover_time_sec

        self.update_shader_variables(time_sec)
        self.update()

        row = (
            f'{timestamp}',
            f'{time_sec}',
            f'{self.shared_stim_parameters.stim_select.value}',
            f'{self.shared_stim_parameters.start_time_sec.value}',
            f'{self.shared_stim_parameters.phototaxis_polarity.value}',
            f'{self.shared_stim_parameters.omr_spatial_period_mm.value}',
            f'{self.shared_stim_parameters.omr_angle_deg.value}',
            f'{self.shared_stim_parameters.omr_speed_mm_per_sec.value}',
            f'{self.shared_stim_parameters.concentric_spatial_period_mm.value}',
            f'{self.shared_stim_parameters.concentric_speed_mm_per_sec.value}',
            f'{self.shared_stim_parameters.okr_spatial_frequency_deg.value}',
            f'{self.shared_stim_parameters.okr_speed_deg_per_sec.value}',
            f'{self.shared_stim_parameters.looming_center_mm[0]}',
            f'{self.shared_stim_parameters.looming_center_mm[1]}',
            f'{self.shared_stim_parameters.looming_period_sec.value}',
            f'{self.shared_stim_parameters.looming_expansion_time_sec.value}',
            f'{self.shared_stim_parameters.looming_expansion_speed_mm_per_sec.value}',
            f'{self.shared_stim_parameters.dot_center_mm[0]}',
            f'{self.shared_stim_parameters.dot_center_mm[1]}',
            f'{self.shared_stim_parameters.dot_radius_mm.value}',
            f'{self.shared_stim_parameters.n_preys.value}',
            f'{self.shared_stim_parameters.prey_speed_mm_s.value}',
            f'{self.shared_stim_parameters.prey_radius_mm.value}'
        )
        self.fd.write(','.join(row) + '\n')

    def process_data(self, data) -> None:
        # this runs in the worker process

        # TODO use get instead of try except ?
        if data is None:
            return
        
        try:
            if not data['tracking']['success']:
                return
            
            fields = data['tracking'].dtype.names

            print(f"frame {data['index']}, fish {data['identity']}: latency {1e-6*(time.perf_counter_ns() - data['timestamp'])}")
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

    def process_metadata(self, metadata) -> None:
        # this runs in the worker process
        
        control: Dict = metadata['visual_stim_control']
        
        if control is None:
            return
        
        timestamp = time.perf_counter_ns()
        timestamp_sec = 1e-9*timestamp
        time_sec = timestamp_sec % self.rollover_time_sec
        control['time_sec'] = time_sec

        self.shared_stim_parameters.from_dict(control)
