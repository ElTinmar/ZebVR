from vispy import gloo, app
from typing import Tuple, List, Callable
import sys
from multiprocessing import Process, RawArray
import time
import numpy as np
import json
from image_tools import im2single, im2rgb, im2uint8, im2gray
import cv2
from numpy.typing import NDArray
from image_tools import regular_polygon, star

RESIZED_HEIGHT = 512 # make sure that display fits on various screens

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

def create_calibration_pattern(div: int, height: int, width: int, pattern_intensity: int) -> NDArray:
    
    step = min(height,width)//div
    calibration_pattern = np.zeros((height,width,3), np.uint8)

    for y in range(height//(2*div),height,step):
        for x in range(width//(2*div),width,step):

            n = np.random.randint(3,7)
            s = np.random.randint(step//4, step//2)
            pos = np.array([x,y])
            theta = 2*np.pi*np.random.rand()

            if np.random.rand()>0.5:
                poly = regular_polygon(pos,n,theta,s)
            else:
                poly = star(pos,n,theta,s//2,s)

            calibration_pattern = cv2.fillPoly(
                calibration_pattern, 
                pts=[poly], 
                color=(pattern_intensity, pattern_intensity, pattern_intensity)
            )
    
    return calibration_pattern

def check_registration(
    camera_constructor: Callable,
    exposure_microsec: int,
    cam_height: int,
    cam_width: int,
    gain: float,
    fps: int,
    height: int,
    width: int,
    offset_x: int,
    offset_y: int,
    proj_width: int,
    proj_height: int,
    proj_pos: Tuple[int, int],
    registration_file: str, 
    pattern_intensity: int = 128,       
    pattern_grid_size: int = 5,
    pixel_scaling: Tuple[float, float] = (1.0, 1.0), # only for exotic devices such as Lightcrafters in native mode
    ):

    proj = Projector(
        window_size=(proj_width, proj_height), 
        window_position=proj_pos, 
        pixel_scaling=pixel_scaling
    )
    proj.start()

    camera = camera_constructor()
    camera.set_exposure(exposure_microsec)
    camera.set_gain(gain)
    camera.set_framerate(fps)
    camera.set_height(height)
    camera.set_width(width)
    camera.set_offsetX(offset_x)
    camera.set_offsetY(offset_y)

    print(f'Loading pre-existing calibration: {registration_file}')
    with open(registration_file, 'r') as f:
        calibration = json.load(f)

    print(json.dumps(calibration, indent=2))

    cam_to_proj = np.array(calibration['cam_to_proj'], dtype=np.float32)

    pattern = create_calibration_pattern(
        pattern_grid_size, 
        cam_height, 
        cam_width, 
        pattern_intensity
    )
    mask_cam = im2single(im2gray(pattern))
    mask_proj = cv2.warpAffine(mask_cam, cam_to_proj[:2,:],(proj_width, proj_height)) # dsize = (cols,rows)

    # project point        
    proj.draw_image(mask_proj)
    time.sleep(0.1)

    # get camera frame 
    camera.start_acquisition() 
    frame = camera.get_frame()
    camera.stop_acquisition()        
    image = im2rgb(frame.image)
    image[:,:,0] = im2uint8(mask_cam)

    resized_width = int(RESIZED_HEIGHT * width/height)
    disp = cv2.resize(image,(resized_width, RESIZED_HEIGHT))
    print('Press key to close...')
    cv2.imshow('calibration test', disp)
    cv2.waitKey(10_000) 
    cv2.destroyAllWindows() 
        
    proj.terminate()
    
if __name__ == '__main__':

    from ZebVR.config import ( 
        CAMERA_CONSTRUCTOR,
        CAM_WIDTH, 
        CAM_HEIGHT,
        CAM_EXPOSURE_MS, 
        CAM_GAIN, 
        CAM_FPS,
        CAM_OFFSETX, 
        CAM_OFFSETY, 
        PROJ_WIDTH, 
        PROJ_HEIGHT, 
        PROJ_POS,
        PATTERN_INTENSITY, 
        PIXEL_SCALING, 
        REGISTRATION_FILE
    )

    check_registration(
        camera_constructor=CAMERA_CONSTRUCTOR,
        exposure_microsec=CAM_EXPOSURE_MS,
        gain=CAM_GAIN,
        fps=CAM_FPS,
        height=CAM_HEIGHT,
        width=CAM_WIDTH,
        offset_x=CAM_OFFSETX,
        offset_y=CAM_OFFSETY,
        proj_width=PROJ_WIDTH,
        proj_height=PROJ_HEIGHT,
        proj_pos=PROJ_POS,
        cam_height=CAM_HEIGHT,
        cam_width=CAM_WIDTH,
        registration_file=REGISTRATION_FILE,
        pattern_grid_size=5,
        pattern_intensity=PATTERN_INTENSITY,
        pixel_scaling=PIXEL_SCALING
    )
    
