from vispy import gloo, app
from typing import Tuple
import sys
from multiprocessing import Process, Value
import time
import numpy as np
import json
from camera_tools import XimeaCamera
from image_tools import im2single, enhance, im2rgb, im2uint8, im2gray
import cv2
from geometry import to_homogeneous
from tqdm import tqdm
import os

VERT_SHADER_CALIBRATION = """
attribute float a_radius;
attribute vec2 a_point;
attribute vec2 a_position;

varying vec2 v_point;
varying float v_radius;

void main()
{
    gl_Position = vec4(a_position, 0.0, 1.0);
    v_point = a_point;
    v_radius = a_radius;
} 
"""

FRAG_SHADER_CALIBRATION = """
varying vec2 v_point;
varying float v_radius;

void main()
{
    if (distance(gl_FragCoord.xy,v_point) <= v_radius) {
        gl_FragColor = vec4(1.0,1.0,1.0,1.0);
    }
}
"""

class Projector(app.Canvas, Process):

    def __init__(
            self, 
            window_size: Tuple[int, int] = (1280, 720),
            window_position: Tuple[int, int] = (0,0),
            window_decoration: bool = False,
            radius: int = 10,
            *args,
            **kwargs
        ) -> None:
            
            Process.__init__(self, *args, **kwargs)
            
            self.window_size = window_size
            self.window_position = window_position
            self.window_decoration = window_decoration 
            self.radius = radius
            self.x = Value('f', 0)
            self.y = Value('f', 0)

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

        # set attributes, these must be present in the vertex shader
        self.program['a_radius'] = self.radius
        self.program['a_point'] =  [0, 0]
        self.program['a_position'] = [(-1, -1), (-1, +1),
                                    (+1, -1), (+1, +1)]
        
        self.timer = app.Timer('auto', self.on_timer)
        self.timer.start()
        self.show()

    def on_timer(self, event):
        self.program['a_point'] = [self.x.value, self.y.value]
        self.update()

    def on_draw(self, event):
        gloo.clear('black')
        self.program.draw('triangle_strip')

    def draw_point(self, x: int, y: int):
        self.x.value = x
        self.y.value = y

    def run(self):
        self.initialize()
        if sys.flags.interactive != 1:
            app.run()

if __name__ == '__main__':

    # TODO create polygons in cam coords, transform and project 
    # display RGB with two different channels, what's expected from cam coords and what you get out of the projector
    # this requires to change the shaders to display a mask instead of points
    
    PROJ_HEIGHT = 912
    PROJ_WIDTH = 1140
    PROJ_POS = (2560,0)

    CAM_EXPOSURE_MS = 10000
    CAM_GAIN = 0
    CAM_FPS = 10
    CAM_HEIGHT = 2048
    CAM_WIDTH = 2048
    CAM_OFFSETX = 0
    CAM_OFFSETY = 0

    DETECTION_TRESHOLD = 0.2
    CONTRAST = 1
    GAMMA = 1
    BRIGHTNESS = 0
    BLUR_SIZE_PX = 3
    DOT_RADIUS = 1
    STEP_SIZE = 200

    CALIBRATION_FILE = 'calibration.json'

    proj = Projector(window_size=(PROJ_WIDTH, PROJ_HEIGHT), window_position=PROJ_POS, radius=DOT_RADIUS)
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
        prev_cal = json.load(f)

    cam_to_proj = np.array(prev_cal['cam_to_proj'])
    X,Y = np.mgrid[100:CAM_WIDTH:STEP_SIZE, 100:CAM_HEIGHT:STEP_SIZE]
    pts_cam = np.vstack([X.ravel(), Y.ravel(), np.ones(X.size)])
    pts_proj = cam_to_proj @ pts_cam

    pts_proj = pts_proj[:2,:].T
    pts_cam = pts_cam[:2,:].T
    
    cv2.namedWindow('calibration test')

    # make sure that everything is initialized
    time.sleep(1)

    for idx, pts in tqdm(enumerate(zip(pts_proj, pts_cam))):
        
        p_proj, p_cam = pts

        # project point
        proj.draw_point(*p_proj)

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
        image = cv2.circle(image, p_cam[::-1].astype(np.int32), 4, (0,255,0),-1)

        cv2.imshow('calibration test', image)
        cv2.waitKey(1)
        

    proj.terminate()
    camera.stop_acquisition()
    cv2.destroyAllWindows()

    
