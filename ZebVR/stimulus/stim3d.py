from typing import Tuple
from .visual_stim import VisualStim
from vispy import gloo, app, use
from vispy.util.transforms import translate, rotate, frustum, ortho
from vispy.geometry import create_box
from vispy.io import imread, read_mesh
from multiprocessing import RawValue, RawArray
import time
import numpy as np 
from dataclasses import dataclass
from geometry import AffineTransform2D
from multiprocessing import Event 

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

def lookAt(eye, target, up=[0, 1, 0]):
    """Computes matrix to put eye looking at target point."""

    eye = np.asarray(eye).astype(np.float32)
    target = np.asarray(target).astype(np.float32)
    up = np.asarray(up).astype(np.float32)

    forward = target - eye
    forward /= np.linalg.norm(forward)

    side = np.cross(forward, up)
    side /= np.linalg.norm(side)

    up = np.cross(side, forward)

    M = np.eye(4)
    M[0,:3] = side
    M[1,:3] = up
    M[2,:3] = -forward
    M[0,3] = -np.dot(side, eye)
    M[1,3] = -np.dot(up, eye)
    M[2,3] = np.dot(forward, eye)
    
    return M

use(gl='gl+')

VERT_SHADER = """
#version 140
  
// uniforms
uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;
uniform mat4 u_lightspace;
uniform vec3 u_fish;
uniform vec3 u_screen_bottomleft;
uniform vec3 u_screen_normal;

// per-vertex attributes
attribute vec3 a_position;
attribute vec2 a_texcoord;
attribute vec3 a_normal;

// per-instance attribute
attribute vec3 a_instance_shift;

// varying
varying float v_depth;
varying vec2 v_texcoord;
varying vec3 v_normal_world;
varying vec4 v_world_position;
varying vec4 v_lightspace_position;

vec3 plane_proj(vec3 fish_pos, vec3 vertex_pos, vec3 screen_bottomleft, vec3 screen_normal) { 

    // vertex coords
    float x_v = vertex_pos.x;
    float y_v = vertex_pos.y;
    float z_v = vertex_pos.z;

    // fish coords
    float x_f = fish_pos.x;
    float y_f = fish_pos.y;
    float z_f = fish_pos.z;

    // plane
    float a = screen_normal.x;
    float b = screen_normal.y;
    float c = screen_normal.z;
    float d = -dot(screen_normal, screen_bottomleft);

    float denominator = dot(screen_normal, fish_pos-vertex_pos);
    // TODO handle degenerate case?

    float x = (b*(x_v*y_f - x_f*y_v) + c*(x_v*z_f - x_f*z_v) + d*(x_v-x_f)) / denominator;
    float y = (a*(y_v*x_f - y_f*x_v) + c*(y_v*z_f - y_f*z_v) + d*(y_v-y_f)) / denominator;
    float z = (a*(z_v*x_f - z_f*x_v) + b*(z_v*y_f - z_f*y_v) + d*(z_v-z_f)) / denominator;

    vec3 sol = vec3(x, y, z);
    return sol;
}

void main()
{
    vec4 vertex_world = u_model * vec4(a_position, 1.0);
    vertex_world.xyz = vertex_world.xyz + a_instance_shift;  
    vec3 screen_world = plane_proj(u_fish, vertex_world.xyz, u_screen_bottomleft, u_screen_normal);
    vec3 normal_world = transpose(inverse(mat3(u_model))) * a_normal;
    vec4 screen_clip = u_projection * u_view * vec4(screen_world, 1.0);

    float magnitude = length(vertex_world.xyz - u_fish);
    vec3 direction = normalize(screen_world - u_fish);
    float orientation = sign(dot(vertex_world.xyz - u_fish, screen_world - u_fish));

    vec3 offset_world = u_fish;
    offset_world += orientation*direction * magnitude;
    vec4 offset_clip = u_projection * u_view * vec4(offset_world, 1.0);

    v_depth = offset_clip.z/offset_clip.w;
    v_texcoord = a_texcoord;
    v_normal_world = normal_world;
    v_world_position = vertex_world;
    v_lightspace_position = u_lightspace * vertex_world;
    gl_Position = screen_clip;
}
"""

FRAG_SHADER = """
#version 140

uniform sampler2D u_texture;
uniform sampler2D u_shadow_map_texture;
uniform vec2 u_resolution;
uniform vec3 u_light_position;
uniform vec3 u_fish;

varying vec3 v_normal_world;
varying vec2 v_texcoord;
varying float v_depth;
varying vec4 v_world_position;
varying vec4 v_lightspace_position;

float get_shadow(vec4 lightspace_position,  vec3 norm, vec3 light_direction)
{
    float bias = mix(0.05, 0.0, dot(norm, light_direction));    

    vec3 position_ndc = lightspace_position.xyz / lightspace_position.w;
    position_ndc = position_ndc * 0.5 + 0.5;
    
    float closest_depth = texture2D(u_shadow_map_texture, position_ndc.xy).r; 
    float current_depth = position_ndc.z;
    float shadow = 0.0;

    if ( position_ndc.z > 1.0 || 
        position_ndc.x < 0.0 || position_ndc.x > 1.0 ||
        position_ndc.y < 0.0 || position_ndc.y > 1.0
    ) {
        return shadow;
    }

    vec2 texelSize = 1.0 / textureSize(u_shadow_map_texture, 0);
    for(int x = -1; x <= 1; ++x) {
        for(int y = -1; y <= 1; ++y) {
            float pcfDepth = texture2D(u_shadow_map_texture, position_ndc.xy + vec2(x, y) * texelSize).r; 
            shadow += (current_depth - bias) > pcfDepth ? 1.0 : 0.0;        
        }    
    }
    shadow /= 9.0;

    return shadow;
}

vec4 Blinn_Phong(vec3 object_color, vec3 normal, vec3 fragment_position, vec3 view_position, vec3 light_position, vec4 lightspace_position) {

    float enable_shadows = 1.0;

    vec3 ambient_color = vec3(1.0, 1.0, 1.0);
    vec3 diffuse_color = vec3(1.0, 1.0, 1.0);
    vec3 specular_color = vec3(1.0, 1.0, 1.0);

    // ambient
    float light_ambient = 0.1;
    vec3 ambient = light_ambient * ambient_color;

    // diffuse
    vec3 norm = normalize(normal); 
    vec3 light_direction = normalize(light_position - fragment_position);  
    float lambertian = max(dot(norm, light_direction), 0.0); 
    vec3 diffuse = lambertian * diffuse_color;

    // specular
    float light_specular = 0.5;
    float light_shininess = 32;

    vec3 view_direction = normalize(view_position - fragment_position);
    vec3 half_vector = normalize(view_direction + light_direction);
    float specular_angle = max(dot(half_vector, normal), 0.0);
    float spec = pow(specular_angle, light_shininess);
    vec3 specular = light_specular * spec * specular_color;  

    // Blinn_Phong shading
    vec3 result;
    if (enable_shadows == 1.0) {
        float shadow = get_shadow(lightspace_position, norm, light_direction);
        result = (ambient + (1.0 - shadow) * (diffuse + specular)) * object_color;
    }
    else {
        result = (ambient + diffuse + specular) * object_color;
    }
    return vec4(result, 1.0);
}

void main()
{
    float gamma = 2.2;

    // texture
    vec4 object_color = texture2D(u_texture, v_texcoord);

    // lighting
    vec4 phong_shading = Blinn_Phong(vec3(object_color), v_normal_world, vec3(v_world_position), u_fish, u_light_position, v_lightspace_position);

    // gamma correction    
    vec4 gamma_corrected = phong_shading;
    gamma_corrected.rgb = pow(gamma_corrected.rgb, vec3(1.0/gamma));
    
    // debug shadow
    //vec3 position_ndc = v_lightspace_position.xyz / v_lightspace_position.w;
    //position_ndc = position_ndc * 0.5 + 0.5;
    //float closest_depth = texture2D(u_shadow_map_texture, position_ndc.xy).r; 
    //gl_FragColor = vec4(vec3(closest_depth), 1.0);

    // debug texture
    //gl_FragColor = vec4(v_texcoord,0,1);

    gl_FragColor = gamma_corrected;
    gl_FragDepth = v_depth;
}
"""

VERTEX_SHADER_SHADOW="""
#version 140

uniform mat4 u_model;
uniform mat4 u_lightspace;

attribute vec3 a_position;
attribute vec2 a_texcoord;
attribute vec3 a_normal;
attribute vec3 a_instance_shift;

// need to make sure attributes are not optimized away causing some weird shift
varying vec2 v_texcoord;
varying vec3 v_normal_world;

void main()
{
    v_texcoord = a_texcoord;
    v_normal_world = a_normal;
    vec4 world_pos = u_model * vec4(a_position, 1.0);
    world_pos.xyz = world_pos.xyz + a_instance_shift;
    gl_Position = u_lightspace * world_pos;
}
"""

FRAGMENT_SHADER_SHADOW="""
#version 140

void main()
{
    float depth = gl_FragCoord.z;
    gl_FragColor = vec4(depth,0.0,0.0,1.0);
}
"""

SHELL_MODEL = rotate(90,(1,0,0)).dot(rotate(180,(0,0,1))).dot(translate((0,0.6,0)))
GROUND_MODEL = translate((0,0,-15))
SHADOWMAP_RES = 4096

class Stim3D(app.Canvas):

    def __init__(
            self,  
            window_size: Tuple[int, int], 
            window_position: Tuple[int, int], 
            camera_resolution: Tuple[int, int],
            window_decoration: bool = False,
            transformation_matrix: AffineTransform2D = AffineTransform2D.identity(),
            pixel_scaling: Tuple[float, float] = (1.0,1.0),
            pix_per_mm: float = 30,
            refresh_rate: int = 120,
            vsync: bool = False,
            fullscreen: bool = True,
            num_tail_points_interp: int = 40,
        ) -> None:

        self.window_size = window_size
        self.window_position = window_position
        self.camera_resolution = camera_resolution
        self.window_decoration = window_decoration
        self.transformation_matrix = transformation_matrix
        self.pixel_scaling = pixel_scaling
        self.pix_per_mm = pix_per_mm
        self.vsync = vsync
        self.use_fullscreen = fullscreen

        self.num_tail_points_interp = num_tail_points_interp

        self.shared_fish_state = SharedFishState(num_tail_points_interp)
        self.refresh_rate = refresh_rate
        self.tstart = 0

        self.x = 0
        self.y = 0
        self.z = 65

        # TODO fix this
        self.screen_width_cm = 60 
        self.screen_height_cm = 34
        self.screen_bottomleft = [-self.screen_width_cm//2,0,0]
        self.screen_normal = [0,0,1]
        self.screen_bottomleft_x, self.screen_bottomleft_y, self.screen_bottomleft_z = self.screen_bottomleft
        
        self.light_theta = 0
        self.light_theta_step = 0.01
        self.t = 0
        self.t_step = 1/30

        self.initialized = Event()

    def initialize(self):
        # this needs to happen in the process where the window is displayed

        app.Canvas.__init__(
            self, 
            size = self.window_size, 
            decorate = self.window_decoration, 
            position = self.window_position, 
            keys = 'interactive', 
            vsync = self.vsync,
            fullscreen = self.use_fullscreen,
            always_on_top = True,
        )

        self.set_context()
        self.create_view()
        self.create_projection()
        self.create_scene()

        self.timer = app.Timer(1/30, connect=self.on_timer, start=True)
        self.update_shader_variables()
        self.show()

        self.initialized.set()

    def cleanup(self):
        self.initialized.clear()
            
    def set_context(self):
        self.width, self.height = self.window_size
        gloo.set_viewport(0, 0, self.width, self.height)
        gloo.set_state(depth_test=True)  # required for object in the Z axis to hide each other

    def create_view(self):
        # if using an LCD it does not matter so much. 
        # match distance if you use an actual projector
        self.view = translate((0, 0, -100))

    def create_projection(self):
        left = self.screen_bottomleft_x
        bottom = self.screen_bottomleft_y
        depth = self.screen_bottomleft_z-(-100)
        right = left + self.screen_width_cm
        top = bottom + self.screen_height_cm
        znear = 1
        zfar = 1000
        scale = znear/abs(depth)
        
        self.projection = frustum(scale*left, scale*right, scale*bottom, scale*top, znear, zfar)

    def create_scene(self):

        light_position = [5,5,5]
        light_projection = ortho(-50,50,-50,50,1,30)
        light_view = lookAt(light_position, [0,0,0], [0,1,0])
        lightspace = light_projection.T @ light_view    
        lightspace = lightspace.T

        # set up shadow map buffer
        self.shadow_map_texture = gloo.Texture2D(
            data = ((SHADOWMAP_RES, SHADOWMAP_RES, 3)), 
            format = 'rgb',
            interpolation = 'nearest',
            wrapping = 'repeat',
            internalformat = 'rgb32f'
        )
        # attach texture as depth buffer
        self.fbo = gloo.FrameBuffer(color = self.shadow_map_texture)

        ## ground ----------------------------------------------------------------------------

        # load texture
        texture = np.flipud(imread('ZebVR/resources/sand.jpeg'))

        vertices, faces, _ = create_box(width=30, height=30, depth=1, height_segments=100, width_segments=100, depth_segments=10)
        vtype = [
            ('a_position', np.float32, 3),
            ('a_texcoord', np.float32, 2),
            ('a_normal', np.float32, 3)
        ]
        vertex = np.zeros(vertices.shape[0], dtype=vtype)
        vertex['a_position'] = vertices['position']
        vertex['a_texcoord'] = vertices['texcoord']*2
        vertex['a_normal'] = vertices['normal']
        vbo_ground = gloo.VertexBuffer(vertex, divisor=0)
        self.ground_indices = gloo.IndexBuffer(faces)
        instance_shift = gloo.VertexBuffer(np.array([[0,0,0],[15,0,15],[-15,0,-30]], np.float32), divisor=1)

        self.shadowmap_ground = gloo.Program(VERTEX_SHADER_SHADOW, FRAGMENT_SHADER_SHADOW)
        self.shadowmap_ground.bind(vbo_ground) 
        self.shadowmap_ground['u_model'] = GROUND_MODEL
        self.shadowmap_ground['u_lightspace'] = lightspace
        self.shadowmap_ground['a_instance_shift'] = instance_shift
        
        self.ground_program = gloo.Program(VERT_SHADER, FRAG_SHADER)
        self.ground_program.bind(vbo_ground) 
        self.ground_program['u_fish'] = [0, 0, 0]
        self.ground_program['u_texture'] = gloo.Texture2D(texture, wrapping='repeat')
        self.ground_program['a_instance_shift'] = instance_shift
        self.ground_program['u_resolution'] = [self.width, self.height]
        self.ground_program['u_view'] = self.view
        self.ground_program['u_model'] = GROUND_MODEL
        self.ground_program['u_projection'] = self.projection
        self.ground_program['u_lightspace'] = lightspace
        self.ground_program['u_light_position'] = light_position
        self.ground_program['u_shadow_map_texture'] = self.shadow_map_texture
        self.ground_program['u_screen_normal'] = self.screen_normal
        self.ground_program['u_screen_bottomleft'] = self.screen_bottomleft

        ## shell -----------------------------------------------------------------------------

        # load texture
        texture = np.flipud(imread('ZebVR/resources/quartz.jpg'))

        # load mesh
        vertices, faces, normals, texcoords = read_mesh('ZebVR/resources/shell_simplified.obj')
        vertices = 10*vertices
        vtype = [
            ('a_position', np.float32, 3),
            ('a_texcoord', np.float32, 2),
            ('a_normal', np.float32, 3)
        ]
        vertex = np.zeros(vertices.shape[0], dtype=vtype)
        vertex['a_position'] = vertices
        vertex['a_texcoord'] = texcoords
        vertex['a_normal'] = normals
        vbo_shell = gloo.VertexBuffer(vertex, divisor=0)
        self.indices = gloo.IndexBuffer(faces)
        instance_shift = gloo.VertexBuffer(np.array([[10,0,-2],[0,1,-10],[0,5,10],[-5,5,-1]], dtype=np.float32), divisor=1)

        self.shadowmap_program = gloo.Program(VERTEX_SHADER_SHADOW, FRAGMENT_SHADER_SHADOW)
        self.shadowmap_program.bind(vbo_shell)
        self.shadowmap_program['u_model'] = SHELL_MODEL
        self.shadowmap_program['u_lightspace'] = lightspace
        self.shadowmap_program['a_instance_shift'] = instance_shift

        self.main_program = gloo.Program(VERT_SHADER, FRAG_SHADER)
        self.main_program.bind(vbo_shell)
        self.main_program['u_texture'] = texture
        self.main_program['u_fish'] = [0,0,0]
        self.main_program['a_instance_shift'] = instance_shift
        self.main_program['u_resolution'] = [self.width, self.height]
        self.main_program['u_view'] = self.view
        self.main_program['u_model'] = SHELL_MODEL
        self.main_program['u_projection'] = self.projection
        self.main_program['u_lightspace'] = lightspace
        self.main_program['u_light_position'] = light_position
        self.main_program['u_shadow_map_texture'] = self.shadow_map_texture
        self.main_program['u_screen_normal'] = self.screen_normal
        self.main_program['u_screen_bottomleft'] = self.screen_bottomleft

    def set_filename(self, filename:str):
        self.timings_file = filename

    def update_shader_variables(self):
        # communication between CPU and GPU for every frame drawn

        x, y = self.shared_fish_state.fish_centroid[:]

        # TODO fix that
        # Transform camera space to world coordinates
        pos = np.array((x, y, self.z, 1.0))
        T = np.eye(4)
        T[0,0] = -1/self.pix_per_mm
        T[1,1] = -1/self.pix_per_mm
        T[:3,3] = [self.camera_resolution[0]/(2*self.pix_per_mm),self.camera_resolution[1]/(2*self.pix_per_mm),0]
        pos_world = T @ pos
        self.x, self.y = pos_world[:2]

        self.ground_program['u_fish'] = [self.x, self.y, self.z]
        self.main_program['u_fish'] = [self.x, self.y, self.z]

    def on_draw(self, event):
        # draw to the fbo 
        with self.fbo: 
            gloo.clear(color=True, depth=True)
            gloo.set_viewport(0, 0, SHADOWMAP_RES, SHADOWMAP_RES)
            gloo.set_cull_face('front')
            self.shadowmap_ground.draw('triangles', self.ground_indices)
            self.shadowmap_program.draw('triangles', self.indices)
            
        # draw to screen
        gloo.clear(color=True, depth=True)
        gloo.set_viewport(0, 0, self.width, self.height)
        gloo.set_cull_face('back')
        self.ground_program.draw('triangles', self.ground_indices)
        self.main_program.draw('triangles', self.indices)
        self.update()

    def on_timer(self, event):
        # this runs in the display process

        self.t += self.t_step
        self.light_theta += self.light_theta_step

        light_position =  [10*np.cos(self.light_theta), 20, 10*np.sin(self.light_theta)]
        light_projection = ortho(-100,100,-100,100,1,40)
        light_view = lookAt(light_position, [0,0,0], [0,1,0])
        lightspace = light_projection.T @ light_view
        lightspace = lightspace.T

        self.shadowmap_ground['u_lightspace'] = lightspace
        self.shadowmap_program['u_lightspace'] = lightspace
        self.ground_program['u_lightspace'] = lightspace
        self.ground_program['u_light_position'] = light_position
        self.main_program['u_lightspace'] = lightspace
        self.main_program['u_light_position'] = light_position

        self.update_shader_variables()
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

            print(f"frame {data['index']}, fish {data['identity']}: latency {1e-6*(time.perf_counter_ns() - data['timestamp'])}")

            if 'body' in fields and data['tracking']['body']['success']:
                self.shared_fish_state.fish_centroid[:] = self.transformation_matrix.transform_points(data['tracking']['body']['centroid_global']).squeeze()
                body_axes = data['tracking']['body']['body_axes_global']                
                self.shared_fish_state.fish_caudorostral_axis[:] = self.transformation_matrix.transform_vectors(body_axes[:,0]).squeeze()
                self.shared_fish_state.fish_mediolateral_axis[:] = self.transformation_matrix.transform_vectors(body_axes[:,1]).squeeze()
            else:
                self.shared_fish_state.fish_centroid[:] =  self.transformation_matrix.transform_points(data['tracking']['animals']['centroids_global']).squeeze()

            # TODO use eyes heading vector if present?
            # eyes
            if 'eyes' in fields and data['tracking']['eyes']['success']:

                if data['tracking']['eyes']['left_eye'] is not None:
                    self.shared_fish_state.left_eye_centroid[:] = self.transformation_matrix.transform_points(data['tracking']['eyes']['left_eye']['centroid_cropped']).squeeze()
                    self.shared_fish_state.left_eye_angle.value = data['tracking']['eyes']['left_eye']['angle']

                if data['tracking']['eyes']['right_eye'] is not None:
                    self.shared_fish_state.right_eye_centroid[:] =  self.transformation_matrix.transform_points(data['tracking']['eyes']['right_eye']['centroid_cropped']).squeeze()
                    self.shared_fish_state.right_eye_angle.value = data['tracking']['eyes']['right_eye']['angle']

            # tail
            if 'tail' in fields and data['tracking']['tail']['success']:
                skeleton_interp = self.transformation_matrix.transform_points(data['tracking']['tail']['skeleton_interp_cropped'])
                self.shared_fish_state.tail_points[:self.num_tail_points_interp] = skeleton_interp[:,0]
                self.shared_fish_state.tail_points[self.num_tail_points_interp:] = skeleton_interp[:,1]

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
        pass