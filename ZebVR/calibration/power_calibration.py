from vispy import gloo, app
from typing import Tuple, Callable, NamedTuple
import sys
from multiprocessing import Process, RawArray
import time
from thorlabs_pmd import TLPMD, Bandwidth, LineFrequency
import numpy as np
import pickle

class PowerCalibration(NamedTuple):
    x: np.ndarray
    y: np.ndarray
    y_pred: np.ndarray
    slope: float
    intercept: float
    r_squared: float

VERT_SHADER_CALIBRATION = """
attribute vec2 a_position;
attribute vec4 a_color;
varying vec4 v_color;

void main()
{
    gl_Position = vec4(a_position, 0.0, 1.0);
    v_color = a_color;
} 
"""

FRAG_SHADER_CALIBRATION = """
varying vec4 v_color;

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
    gl_FragColor = linear_to_srgb(v_color);
}
"""

class Projector(app.Canvas, Process):

    def __init__(
            self, 
            window_size: Tuple[int, int] = (1280, 720),
            window_position: Tuple[int, int] = (0,0),
            window_decoration: bool = False,
            fullscreen: bool = True,
            *args,
            **kwargs
        ) -> None:
            
            Process.__init__(self, *args, **kwargs)
            
            self.window_size = window_size
            self.window_position = window_position
            self.window_decoration = window_decoration 
            self._fullscreen_flag = fullscreen
            self.color = RawArray('f', [0,0,0,1])

    def initialize(self):
        # this needs to happen in the process where the window is displayed

        app.Canvas.__init__(
            self, 
            size = self.window_size, # (width, height)
            decorate = self.window_decoration, 
            position = self.window_position,
            fullscreen = self._fullscreen_flag, 
            keys='interactive'
        )

        self.program = gloo.Program(VERT_SHADER_CALIBRATION, FRAG_SHADER_CALIBRATION)
        self.program['a_position'] = [[-1, -1], [-1, 1], [1, -1], [1, 1]]
        self.program['a_color'] = self.color[:]

        self.timer = app.Timer('auto', self.on_timer)
        self.timer.start()
        self.show()

    def on_timer(self, event):
        self.program['a_color'] = self.color[:]
        self.update()

    def on_draw(self, event):
        gloo.clear('black')
        self.program.draw('triangle_strip')

    def set_color(self, color: Tuple[float, float, float, float]):
        self.color[:] = color

    def run(self):
        self.initialize()
        if sys.flags.interactive != 1:
            app.run()
    
def power_calibration(
        powermeter_constructor: Callable[[], TLPMD],
        proj_width: int,
        proj_height: int,
        proj_pos: Tuple[int, int],
        calibration_file: str,
        bandwidth: bool = True,
        attenuation_dB: float = 0,
        range_decade: int = -2,
        average_count: int = 100,
        line_frequency: LineFrequency = LineFrequency.FITFTY_HZ, 
        wavelength_red: float = 610,
        wavelength_green: float = 520,
        wavelength_blue: float = 400,
        num_steps: int = 11, 
        pause: float = 1
    ) -> None:

    x = np.linspace(0,1,num_steps)
    y_red = np.zeros((num_steps,), dtype=np.float32)
    y_green = np.zeros((num_steps,), dtype=np.float32)
    y_blue = np.zeros((num_steps,), dtype=np.float32)

    # set up projector
    proj = Projector(
        window_size = (proj_width, proj_height), 
        window_position = proj_pos, 
    )
    proj.start()

    # set up powermeter
    powermeter = powermeter_constructor()

    # make sure everyone is ready
    time.sleep(5)

    # set parameters
    if bandwidth:
        powermeter.set_bandwidth(Bandwidth.LOW)
    else:
        powermeter.set_bandwidth(Bandwidth.HIGH)

    powermeter.set_attenuation_dB(attenuation_dB)
    powermeter.set_current_range_decade(range_decade)
    powermeter.set_average_count(average_count)
    powermeter.set_line_frequency_Hz(line_frequency)

    # calibrate RGB separately
    powermeter.set_wavelength_nm(wavelength_red)
    for i,r in enumerate(x):
        color = (r,0,0,1.0)
        proj.set_color(color)
        time.sleep(pause)
        y_red[i] = powermeter.get_power_density_microW_cm2()

    powermeter.set_wavelength_nm(wavelength_green)
    for i,g in enumerate(x):
        color = (0,g,0,1.0)
        proj.set_color(color)
        time.sleep(pause)
        y_green[i] = powermeter.get_power_density_microW_cm2()

    powermeter.set_wavelength_nm(wavelength_blue)
    for i,b in enumerate(x):
        color = (0,0,b,1.0)
        proj.set_color(color)
        time.sleep(pause)
        y_blue[i] = powermeter.get_power_density_microW_cm2()

    proj.terminate()
    powermeter.close()

    # linear regression
    A = np.column_stack([x, np.ones_like(x)])
    y = np.column_stack([y_red, y_green, y_blue])
    [slope, icpt], ss_res, rank, s = np.linalg.lstsq(A, y, rcond=None)
    y_pred = A @ np.vstack([slope, icpt])
    y_red_pred, y_green_pred, y_blue_pred = y_pred.T
    ss_tot = np.sum((y - np.mean(y, axis=0))**2, axis=0)
    r_squared_red, r_squared_green, r_squared_blue  = 1 - ss_res/ss_tot

    # save results
    with open(calibration_file, 'wb') as f:
        pickle.dump({
            'calibration_red':  PowerCalibration(x, y_red, y_red_pred, slope[0], icpt[0], r_squared_red),
            'calibration_green': PowerCalibration(x, y_green, y_green_pred, slope[1], icpt[1], r_squared_green),
            'calibration_blue':  PowerCalibration(x, y_blue, y_blue_pred, slope[2], icpt[2], r_squared_blue)
        }, f)

if __name__ == "__main__":

    from functools import partial
    from thorlabs_pmd import list_powermeters
    import matplotlib.pyplot as plt

    powermeters = list_powermeters()
    powermeter_constructor = partial(TLPMD, device_info=powermeters[0])
    filename = 'test.pkl'

    power_calibration(
        powermeter_constructor = powermeter_constructor,
        proj_width = 600,
        proj_height = 600,
        proj_pos = (0,0),
        calibration_file = filename,
        range_decade = -4,
        wavelength_red = 610,
        wavelength_green = 520,
        wavelength_blue = 400,
        num_steps = 11, 
        pause = 0.5
    )

    data = np.load(filename)
    plt.plot(100*data['x'], data['y_red'], color='r')
    plt.plot(100*data['x'], data['y_green'], color='g')
    plt.plot(100*data['x'], data['y_blue'], color='b')
    plt.xlabel("Brightness [%]")
    plt.ylabel("Irradiance [mW/cm²]")
    plt.show()
