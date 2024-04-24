from vispy import app, gloo
from typing import Tuple, Any
import time
from dagline import WorkerNode
from multiprocessing import Process
import sys
from numpy.typing import NDArray
import numpy as np 

class VisualStim(app.Canvas):

    def __init__(
            self, 
            vertex_shader: str, 
            fragment_shader: str,
            window_size: Tuple[int, int],
            window_position: Tuple[int, int],
            window_decoration: bool = False,
            transformation_matrix: NDArray = np.eye(3, dtype=np.float32),
            pixel_scaling: Tuple[float, float] = (1.0,1.0)
        ) -> None:
            
            self.vertex_shader = vertex_shader
            self.fragment_shader = fragment_shader
            self.window_size = window_size
            self.window_position = window_position
            self.window_decoration = window_decoration 
            self.transformation_matrix = transformation_matrix
            self.pixel_scaling = pixel_scaling

    def initialize(self):
        # this needs to happen in the process where the window is displayed

        app.Canvas.__init__(self, size=self.window_size, decorate=self.window_decoration, position=self.window_position, keys='interactive')

        self.program = gloo.Program(self.vertex_shader, self.fragment_shader)

        # set attributes, these must be present in the vertex shader
        self.program['u_transformation_matrix'] = self.transformation_matrix.T
        self.program['a_resolution'] = self.window_size
        self.program['a_time'] = 0
        self.program['a_position'] = [(-1, -1), (-1, +1),
                                    (+1, -1), (+1, +1)]
        self.program['a_pixel_scaling'] = self.pixel_scaling
        
        self.t_start = None
        self.first_frame = True 
            
    def on_draw(self, event):
        if self.first_frame:
            self.t_start = time.monotonic()
            self.first_frame = False

    def on_timer(self, event):
        pass

    def work(self, data: Any) -> None:
        '''define a mapping between the data argument and shader variables'''
        pass

class VisualStimWorker(WorkerNode):

    def __init__(self, stim: VisualStim, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stim = stim
        self.display_process = None

    def run(self) -> None:
        self.stim.initialize()
        if sys.flags.interactive != 1:
            app.run()

    def initialize(self) -> None:
        super().initialize()

        # launch main window loop in a separate process 
        self.display_process = Process(target=self.run)
        self.display_process.start()

    def cleanup(self) -> None:
        self.display_process.terminate()

    def work(self, data: Any) -> None:
        self.stim.work(data)