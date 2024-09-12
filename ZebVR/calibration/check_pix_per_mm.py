from vispy import gloo, app
from typing import Tuple, List
import sys
from multiprocessing import Process, RawArray
import numpy as np
import json
import cv2
from numpy.typing import NDArray
import time

VERT_SHADER_CALIBRATION = """
attribute vec2 a_position;
attribute vec2 a_texcoord;
varying vec2 v_texcoord;

void main (void)
{
    v_texcoord = a_texcoord;
    gl_Position = vec4(a_position,0.0,1.0);
}
"""

FRAG_SHADER_CALIBRATION = """
uniform vec2 u_pixel_scaling;
uniform sampler2D u_texture;
varying vec2 v_texcoord;
void main()
{
    gl_FragColor = texture2D(u_texture, u_pixel_scaling*v_texcoord);
    gl_FragColor.a = 1.0;
}
"""

class Projector(app.Canvas, Process):

    def __init__(
            self, 
            window_size: Tuple[int, int] = (1280, 720),
            window_position: Tuple[int, int] = (0,0),
            window_decoration: bool = False,
            pixel_scaling: Tuple[float, float] = (1.0,1.0),
            *args,
            **kwargs
        ) -> None:
            
            Process.__init__(self, *args, **kwargs)
            
            self.window_size = window_size
            self.pixel_scaling = pixel_scaling
            self.window_position = window_position
            self.window_decoration = window_decoration
            self.image = RawArray('f', int(np.prod(window_size)))

    def initialize(self):
        # this needs to happen in the process where the window is displayed

        app.Canvas.__init__(
            self, 
            size=self.window_size, 
            decorate=self.window_decoration, 
            position=self.window_position, 
            keys='interactive'
        )

        self.program = gloo.Program(VERT_SHADER_CALIBRATION, FRAG_SHADER_CALIBRATION)

        image = np.frombuffer(self.image, dtype=np.float32).reshape(self.window_size[::-1])
        self.texture = gloo.Texture2D(image, interpolation='linear')

        # set attributes, these must be present in the vertex shader
        self.program['a_position'] = np.array([[-1, -1], [-1, 1], [1, -1], [1, 1]], dtype=np.float32)
        self.program['a_texcoord'] = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], dtype=np.float32)
        self.program['u_texture'] = self.texture
        self.program['u_pixel_scaling'] = self.pixel_scaling
        
        self.timer = app.Timer('auto', self.on_timer)
        self.timer.start()
        self.show()

    def on_timer(self, event):
        image = np.frombuffer(self.image, dtype=np.float32).reshape(self.window_size[::-1])
        self.texture.set_data(image)
        self.update()

    def on_draw(self, event):
        gloo.clear('black')
        self.program.draw('triangle_strip')

    def draw_image(self, I: NDArray):
        buffer = np.frombuffer(self.image, dtype=np.float32) 
        buffer[:] = I.ravel()

    def run(self):
        self.initialize()
        if sys.flags.interactive != 1:
            app.run()

def disk(point, center, radius):
    return (point[0]-center[0])**2 + (point[1]-center[1])**2 <= radius**2

def check_pix_per_mm(
    proj_width: int,
    proj_height: int,
    proj_pos: Tuple[int, int],
    cam_height: int,
    cam_width: int,
    pix_per_mm: float,
    size_to_check: List[float],
    registration_file: str,
    thickness: float = 10.0,
    reticle_center: Tuple[float, float] = (0, 0),
    pixel_scaling: Tuple[float, float] = (1.0, 1.0), # only for exotic devices such as Lightcrafters in native mode
    ):
     
    proj = Projector(
        window_size=(proj_width, proj_height), 
        window_position=proj_pos, 
        pixel_scaling=pixel_scaling
    )
    proj.start()

    print(f'Loading pre-existing calibration: {registration_file}')
    with open(registration_file, 'r') as f:
        calibration = json.load(f)

    cam_to_proj = np.array(calibration['cam_to_proj'], dtype=np.float32)

    # create a circle with given radius. Measure that it's the right size in the real world 
    mask_cam = np.zeros((cam_height,cam_width), dtype=np.float32) 
    y,x = np.mgrid[0:cam_height,0:cam_width]
    for d in size_to_check:
        # concentric rings of different diameters centered on camera FOV
        radius = d/2 * pix_per_mm
        ring_ind = disk([x,y],reticle_center,radius+thickness/2) & \
                  ~disk([x,y],reticle_center,radius-thickness/2)
        mask_cam[ring_ind] = 1.0

    # transform to proj space and measure if accurate
    mask_proj = cv2.warpAffine(mask_cam, cam_to_proj[:2,:],(proj_width, proj_height)) # dsize = (cols,rows)

    # project point        
    proj.draw_image(mask_proj)
    
    time.sleep(10)
    proj.terminate()

if __name__ == '__main__':
    
    from ZebVR.config import (
        REGISTRATION_FILE, 
        CAM_WIDTH, 
        CAM_HEIGHT,
        PROJ_WIDTH, 
        PROJ_HEIGHT, 
        PROJ_POS,
        PIXEL_SCALING, 
        PIX_PER_MM, 
        CALIBRATION_CHECK_DIAMETER_MM
    )

    check_pix_per_mm(
        proj_width = PROJ_WIDTH,
        proj_height = PROJ_HEIGHT,
        proj_pos = PROJ_POS,
        cam_height = CAM_HEIGHT,
        cam_width = CAM_WIDTH,
        pix_per_mm = PIX_PER_MM,
        size_to_check = CALIBRATION_CHECK_DIAMETER_MM,
        registration_file = REGISTRATION_FILE,
        thickness = 10.0,
        reticle_center = (CAM_WIDTH//2, CAM_HEIGHT//2),
        pixel_scaling = PIXEL_SCALING, 
    )