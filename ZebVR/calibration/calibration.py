from vispy import gloo, app
from typing import Tuple
import sys
from multiprocessing import Process, Value, Event
import time
import numpy as np
import json
from camera_tools import OpenCV_Webcam
#from camera_tools import XimeaCamera
from image_tools import im2single, enhance, im2rgb, im2uint8, im2gray
import cv2

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
    
    
    PROJ_HEIGHT = 720
    PROJ_WIDTH = 1280

    CAM_EXPOSURE_MS = 1000
    CAM_GAIN = 0
    CAM_FPS = 10
    CAM_HEIGHT = 480
    CAM_WIDTH = 640
    CAM_OFFSETX = 0
    CAM_OFFSETY = 0

    DETECTION_TRESHOLD = 0.2
    CONTRAST = 1
    GAMMA = 1
    BRIGHTNESS = 0
    BLUR_SIZE_PX = 10
    DOT_RADIUS = 10
    STEP_SIZE = 200

    CALIBRATION_FILE = 'calibration.json'

    cv2.namedWindow('calibration')

    proj = Projector(window_size=(PROJ_WIDTH, PROJ_HEIGHT), radius=DOT_RADIUS)
    proj.start()

    camera = OpenCV_Webcam()
    camera.set_exposure(CAM_EXPOSURE_MS)
    camera.set_gain(CAM_GAIN)
    camera.set_framerate(CAM_FPS)
    camera.set_height(CAM_HEIGHT)
    camera.set_width(CAM_WIDTH)
    camera.set_offsetX(CAM_OFFSETX)
    camera.set_offsetY(CAM_OFFSETY)

    X,Y = np.mgrid[0:PROJ_WIDTH:STEP_SIZE,0:PROJ_HEIGHT:STEP_SIZE]
    pts_proj = np.vstack([X.ravel(),Y.ravel()]).T
    pts_cam = np.nan * np.ones_like(pts_proj)

    for idx, pt in enumerate(pts_proj):

        # project point
        proj.draw_point(*pt)
        
        # make sure image is displayed
        time.sleep(1)

        # get camera frame
        frame = camera.get_frame()
        
        # smooth frame
        image = enhance(
            im2single(im2gray(frame.image)),
            contrast=CONTRAST,
            gamma=GAMMA,
            brightness=BRIGHTNESS,
            blur_size_px=BLUR_SIZE_PX,
            medfilt_size_px=None
        )

        # check that dot is detected
        max_intensity = np.max(image)
        if max_intensity >= DETECTION_TRESHOLD:

            # get dot position on image
            pos = np.unravel_index(np.argmax(image), image.shape)
            pts_cam[idx,:] = pos

            image = im2rgb(im2uint8(image))
            overlay = cv2.circle(image, pos[::-1], 4, (0,0,255),-1)
            cv2.imshow('calibration', overlay)
            cv2.waitKey(1)
        
    proj.terminate()
    cv2.destroyAllWindows()

    # compute least-square estimate of the transformation and output to json
    transformation = np.linalg.lstsq(pts_cam, pts_proj, rcond=None)[0]
    calibration = {}
    calibration['proj_to_cam'] = transformation.tolist()
    calibration['cam_to_proj'] = np.linalg.inv(transformation).tolist()
    
    with open(CALIBRATION_FILE,'w') as f:
        json.dump(calibration, f)
    
