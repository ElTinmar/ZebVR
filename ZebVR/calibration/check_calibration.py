from vispy import gloo, app
from typing import Tuple
import sys
from multiprocessing import Process, RawArray
import time
import numpy as np
import json
from camera_tools import XimeaCamera
from image_tools import im2single, enhance, im2rgb, im2uint8, im2gray
import cv2
from numpy.typing import NDArray
from image_tools import regular_polygon, star

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
uniform sampler2D u_texture;
varying vec2 v_texcoord;
void main()
{
    gl_FragColor = texture2D(u_texture, v_texcoord);
    gl_FragColor.a = 1.0;
}
"""

class Projector(app.Canvas, Process):

    def __init__(
            self, 
            window_size: Tuple[int, int] = (1280, 720),
            window_position: Tuple[int, int] = (0,0),
            window_decoration: bool = False,
            *args,
            **kwargs
        ) -> None:
            
            Process.__init__(self, *args, **kwargs)
            
            self.window_size = window_size
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

def create_calibration_pattern(div: int, height: int, width: int) -> NDArray:
    
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

            calibration_pattern = cv2.fillPoly(calibration_pattern, pts=[poly], color=(255, 255, 255))
    
    return calibration_pattern

if __name__ == '__main__':

    # TODO create polygons in cam coords, transform and project 
    # display RGB with two different channels, what's expected from cam coords and what you get out of the projector
    # this requires to change the shaders to display a mask instead of points
    
    PROJ_HEIGHT = 1140
    PROJ_WIDTH = 912
    PROJ_POS = (2560,0)

    CAM_EXPOSURE_MS = 1000
    CAM_GAIN = 0
    CAM_FPS = 10
    CAM_HEIGHT = 2048
    CAM_WIDTH = 2048
    CAM_OFFSETX = 0
    CAM_OFFSETY = 0

    CONTRAST = 1
    GAMMA = 1
    BRIGHTNESS = 0
    BLUR_SIZE_PX = None

    CALIBRATION_FILE = 'calibration.json'

    proj = Projector(window_size=(PROJ_WIDTH, PROJ_HEIGHT), window_position=PROJ_POS)
    proj.start()

    camera = XimeaCamera()
    camera.set_exposure(CAM_EXPOSURE_MS)
    camera.set_gain(CAM_GAIN)
    camera.set_framerate(CAM_FPS)
    camera.set_height(CAM_HEIGHT)
    camera.set_width(CAM_WIDTH)
    camera.set_offsetX(CAM_OFFSETX)
    camera.set_offsetY(CAM_OFFSETY)

    print(f'Loading pre-existing calibration: {CALIBRATION_FILE}')
    with open(CALIBRATION_FILE, 'r') as f:
        calibration = json.load(f)

    print(json.dumps(calibration, indent=2))

    cam_to_proj = np.array(calibration['cam_to_proj'])
    proj_to_cam = np.array(calibration['proj_to_cam'])

    mask_cam = im2single(im2gray(create_calibration_pattern(5, CAM_HEIGHT, CAM_WIDTH)))
    mask_proj = cv2.warpAffine(mask_cam, cam_to_proj[:2,:],(PROJ_WIDTH, PROJ_HEIGHT)) # dsize = (cols,rows)

    # project point        
    proj.draw_image(mask_proj)

    time.sleep(2)

    # get camera frame 
    camera.start_acquisition() # looks like I need to restart to get the last frame with OpenCV...
    frame = camera.get_frame()
    camera.stop_acquisition()
        
    # smooth frame
    image = enhance(
        im2single(im2gray(frame.image)),
        contrast=CONTRAST,
        gamma=GAMMA,
        brightness=BRIGHTNESS,
        blur_size_px=BLUR_SIZE_PX,
        medfilt_size_px=None
    )

    image = im2rgb(im2uint8(image))
    image[:,:,0] = im2uint8(mask_cam)

    cv2.imshow('calibration test', image)
    cv2.waitKey(0)
        
    proj.terminate()
    camera.stop_acquisition()
    cv2.destroyAllWindows()

    
