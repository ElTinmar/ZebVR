from vispy import gloo, app
from typing import Tuple, Callable
import sys
from multiprocessing import Process, Value
import time
import numpy as np
from numpy.typing import NDArray
import json
from image_tools import im2single, enhance, im2rgb, im2uint8, im2gray, bwareafilter_centroids
import cv2
from geometry import to_homogeneous
from enum import IntEnum
from functools import partial

RESIZED_HEIGHT = 512 # make sure that display fits on various screens

class Pattern(IntEnum):
    DOTS = 0
    HBAR = 1
    VBAR = 2

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
uniform vec2 u_pixel_scaling;
uniform int u_pattern;

const int DOTS = 0;
const int HBAR = 1;
const int VBAR = 2;

void main()
{
    gl_FragColor = vec4(0.0,0.0,0.0,1.0);
    vec2 pix_coords = u_pixel_scaling * gl_FragCoord.xy;

    if (u_pattern == DOTS) {
        if (distance(pix_coords, v_point) <= v_radius) {
            gl_FragColor = vec4(1.0,1.0,1.0,1.0);
        }
    }

    if (u_pattern == HBAR) {
        if ( abs(pix_coords.y - v_point.y) <= v_radius ) {
            gl_FragColor = vec4(1.0,1.0,1.0,1.0);
        }
    }
    
    if (u_pattern == VBAR) {
        if ( abs(pix_coords.x - v_point.x) <= v_radius ) {
            gl_FragColor = vec4(1.0,1.0,1.0,1.0);
        }
    }
}
"""

class Projector(app.Canvas, Process):

    def __init__(
            self, 
            window_size: Tuple[int, int] = (1280, 720),
            window_position: Tuple[int, int] = (0,0),
            window_decoration: bool = False,
            pixel_scaling: Tuple[float, float] = (1.0,1.0),
            radius: int = 10,
            *args,
            **kwargs
        ) -> None:
            
            Process.__init__(self, *args, **kwargs)
            
            self.window_size = window_size
            self.window_position = window_position
            self.window_decoration = window_decoration 
            self.pixel_scaling = pixel_scaling
            self.radius = radius
            self.x = Value('f', 0)
            self.y = Value('f', 0)
            self.pattern = Value('i', 0)

    def initialize(self):
        # this needs to happen in the process where the window is displayed

        app.Canvas.__init__(
            self, 
            size=self.window_size, # (width, height)
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
        self.program['u_pixel_scaling'] = self.pixel_scaling
        self.program['u_pattern'] = -1
        
        self.timer = app.Timer('auto', self.on_timer)
        self.timer.start()
        self.show()

    def on_timer(self, event):
        self.program['a_point'] = [self.x.value, self.y.value]
        self.program['u_pattern'] = self.pattern.value
        self.update()

    def on_draw(self, event):
        gloo.clear('black')
        self.program.draw('triangle_strip')

    def draw_point(self, x: int, y: int):
        self.x.value = x
        self.y.value = y
        self.pattern.value = Pattern.DOTS

    def draw_vertical_bar(self, x: int):
        self.x.value = x
        self.pattern.value = Pattern.VBAR

    def draw_horizontal_bar(self, y: int):
        self.y.value = y
        self.pattern.value = Pattern.HBAR

    def run(self):
        self.initialize()
        if sys.flags.interactive != 1:
            app.run()

def proj_bar(
    camera,
    coord: NDArray,
    bar_fun: Callable,
    enhance_fun:Callable
):
    
    intensity_profile = np.zeros_like(coord) 
    camera.start_acquisition() 

    for i, x in enumerate(coord):
        bar_fun(x)
        frame = camera.get_frame()
        image = enhance_fun(im2single(im2gray(frame.image)))
        intensity_profile[i] = np.sum(image)

        (height, width) = image.shape
        resized_width = int(RESIZED_HEIGHT * width/height)
        disp = cv2.resize(image,(resized_width, RESIZED_HEIGHT))
        cv2.imshow('calibration', disp)
        cv2.waitKey(1)
    
    camera.stop_acquisition()

def registration(
    camera_constructor: Callable,
    exposure_microsec: int,
    cam_height: int,
    cam_width: int,
    cam_gain: float,
    fps_bars: int, # Needs to be slow enough for processing of bars
    fps_dots: int, # Needs to be slow enough for processing of dots
    cam_offset_x: int,
    cam_offset_y: int,
    proj_width: int,
    proj_height: int,
    proj_pos: Tuple[int, int],
    registration_file: str, 
    contrast: float,
    brightness: float,
    gamma: float,
    blur_size_px: float,
    dot_radius: float,
    bar_num_steps: int,
    dots_num_steps: int,
    dot_detection_threshold: float,
    pixel_scaling: Tuple[float, float] = (1.0, 1.0), # only for exotic devices such as Lightcrafters in native mode
):
        
    proj = Projector(
        window_size=(proj_width, proj_height), 
        window_position=proj_pos, 
        radius=dot_radius,
        pixel_scaling=pixel_scaling
    )
    proj.start()

    camera = camera_constructor()
    camera.set_exposure(exposure_microsec)
    camera.set_gain(cam_gain)
    camera.set_framerate(fps_bars)
    camera.set_height(cam_height)
    camera.set_width(cam_width)
    camera.set_offsetX(cam_offset_x)
    camera.set_offsetY(cam_offset_y)

    enhance_fun = partial(
        enhance,             
        contrast=contrast,
        gamma=gamma,
        brightness=brightness,
        blur_size_px=blur_size_px,
        medfilt_size_px=None
    )

    cv2.namedWindow('calibration')

    # make sure that everything is initialized
    time.sleep(1)     

    x_range = np.linspace(0, proj_width, bar_num_steps)
    x_intensity = np.zeros((bar_num_steps,))
    y_range = np.linspace(0,proj_height, bar_num_steps)
    y_intensity = np.zeros((bar_num_steps,))

    camera.start_acquisition() 
    for i, x in enumerate(x_range):
        proj.draw_vertical_bar(x)
        frame = camera.get_frame()

        image = enhance(
            im2single(im2gray(frame.image)),
            contrast=contrast,
            gamma=gamma,
            brightness=brightness,
            blur_size_px=blur_size_px,
            medfilt_size_px=None
        )

        x_intensity[i] = np.sum(image)

        disp = cv2.resize(image,(512,512))
        cv2.imshow('calibration', disp)
        cv2.waitKey(1)
    camera.stop_acquisition()

    camera.start_acquisition() 
    for i, y in enumerate(y_range):
        proj.draw_horizontal_bar(y)
        frame = camera.get_frame()

        image = enhance(
            im2single(im2gray(frame.image)),
            contrast=contrast,
            gamma=gamma,
            brightness=brightness,
            blur_size_px=blur_size_px,
            medfilt_size_px=None
        )

        y_intensity[i] = np.sum(image)

        disp = cv2.resize(image,(512,512))
        cv2.imshow('calibration', disp)
        cv2.waitKey(1)
    camera.stop_acquisition()

    vbar = np.argwhere(x_intensity >= np.max(x_intensity)/2)
    x_start, x_stop = x_range[vbar[0]], x_range[vbar[-1]]
    hbar = np.argwhere(y_intensity >= np.max(y_intensity)/2)
    y_start, y_stop = y_range[hbar[0]], y_range[hbar[-1]]

    print(f'Bounding box (topleft, bottomright): {(x_start, y_start),(x_stop, y_stop)}')

    X,Y = np.meshgrid(
        np.linspace(x_start, x_stop, dots_num_steps), 
        np.linspace(y_start, y_stop, dots_num_steps)
    )
    pts_proj = np.vstack([X.ravel(), Y.ravel()]).T
    pts_cam = np.nan * np.ones_like(pts_proj)

    # processing takes longer because of bwareafilter_centroids
    # need a lower frame rate
    camera.set_framerate(fps_dots)
    camera.start_acquisition() 
    for idx, pt in enumerate(pts_proj):
                
        # project point
        proj.draw_point(*pt)

        # get camera frame 
        frame = camera.get_frame()

        # process
        image = enhance(
            im2single(im2gray(frame.image)),
            contrast=contrast,
            gamma=gamma,
            brightness=brightness,
            blur_size_px=blur_size_px,
            medfilt_size_px=None
        )
        
        mask = (image >= dot_detection_threshold)
        centroid = bwareafilter_centroids(
            mask, 
            min_size = 0,
            max_size = 20_000, 
            min_length = 0,
            max_length = 0,
            min_width = 0,
            max_width = 0
        )

        image = im2rgb(im2uint8(image))
        if centroid.size > 0:
            pts_cam[idx,:] = centroid[0,:]
            image = cv2.circle(image, np.int32(centroid[0,:]), 4, (0,0,255), -1)

        disp = cv2.resize(image,(512,512))
        cv2.imshow('calibration', disp)
        cv2.waitKey(1)

    camera.stop_acquisition()

    proj.terminate()
    cv2.destroyAllWindows()

    # remove NaNs
    nans = np.isnan(pts_cam).any(axis=1)
    pts_cam = pts_cam[~nans]
    pts_proj = pts_proj[~nans]

    # compute least-square estimate of the transformation and output to json
    transformation = np.linalg.lstsq(to_homogeneous(pts_cam), to_homogeneous(pts_proj), rcond=None)[0]
    transformation = np.transpose(transformation)
    calibration = {}
    calibration['cam_to_proj'] = transformation.tolist()
    calibration['proj_to_cam'] = np.linalg.inv(transformation).tolist()
    
    with open(registration_file,'w') as f:
        json.dump(calibration, f)

if __name__ == '__main__':

    from ZebVR.config import (
        CAMERA_CONSTRUCTOR, 
        CAM_WIDTH, 
        CAM_HEIGHT,
        CAM_GAIN, 
        CAM_REGISTRATION_EXPOSURE_MS, 
        CAM_REGISTRATION_DOTS_FPS,
        CAM_REGISTRATION_BARS_FPS, 
        CAM_OFFSETX, 
        CAM_OFFSETY, 
        PROJ_WIDTH, 
        PROJ_HEIGHT, 
        PROJ_POS,
        BRIGHTNESS, 
        BLUR_SIZE_PX, 
        CONTRAST, 
        GAMMA,
        DOT_STEPS, 
        DOT_RADIUS, 
        BAR_STEPS,
        DETECTION_THRESHOLD,
        PIXEL_SCALING, 
        REGISTRATION_FILE
    )

    def registration(
        camera_constructor=CAMERA_CONSTRUCTOR,
        exposure_microsec=CAM_REGISTRATION_EXPOSURE_MS,
        cam_height=CAM_HEIGHT,
        cam_width=CAM_WIDTH,
        cam_gain=CAM_GAIN,
        fps_bars=CAM_REGISTRATION_BARS_FPS,
        fps_dots=CAM_REGISTRATION_DOTS_FPS,
        cam_offset_x=CAM_OFFSETX,
        cam_offset_y=CAM_OFFSETY,
        proj_width=PROJ_WIDTH,
        proj_height=PROJ_HEIGHT,
        proj_pos=PROJ_POS,
        registration_file=REGISTRATION_FILE, 
        contrast=CONTRAST,
        brightness=BRIGHTNESS,
        gamma=GAMMA,
        blur_size_px=BLUR_SIZE_PX,
        dot_radius=DOT_RADIUS,
        bar_num_steps=BAR_STEPS,
        dots_num_steps=DOT_STEPS,
        dot_detection_threshold=DETECTION_THRESHOLD,
        pixel_scaling=PIXEL_SCALING
    )


    
