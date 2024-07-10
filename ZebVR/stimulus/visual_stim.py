from vispy import app, gloo
from typing import Tuple, Any
import time
from dagline import WorkerNode
from multiprocessing import Process
from numpy.typing import NDArray
import numpy as np 

# TODO: add proj resolution (mm/pix) to be able to project stimuli 
# of a given real world size. This can be derived from the camera 
# calibration and came/proj registration

class VisualStim(app.Canvas):

    def __init__(
            self, 
            vertex_shader: str, 
            fragment_shader: str,
            window_size: Tuple[int, int],
            window_position: Tuple[int, int],
            window_decoration: bool = False,
            transformation_matrix: NDArray = np.eye(3, dtype=np.float32),
            pixel_scaling: Tuple[float, float] = (1.0,1.0),
            vsync: bool = True
        ) -> None:
            
            self.vertex_shader = vertex_shader
            self.fragment_shader = fragment_shader
            self.window_size = window_size
            self.window_position = window_position
            self.window_decoration = window_decoration 
            self.transformation_matrix = transformation_matrix
            self.pixel_scaling = pixel_scaling
            self.vsync = vsync

    def initialize(self):
        # this needs to happen in the process where the window is displayed

        app.Canvas.__init__(self, size=self.window_size, decorate=self.window_decoration, position=self.window_position, keys='interactive', vsync=self.vsync)

        self.program = gloo.Program(self.vertex_shader, self.fragment_shader)

        # set attributes, these must be present in the vertex shader
        self.program['u_transformation_matrix'] = self.transformation_matrix.T
        self.program['a_resolution'] = self.window_size
        self.program['a_time'] = 0
        self.program['a_position'] = [(-1, -1), (-1, +1),
                                    (+1, -1), (+1, +1)]
        self.program['u_pixel_scaling'] = self.pixel_scaling
        
        self.t_start = None
        self.first_frame = True 

    def cleanup(self):
        pass
            
    def on_draw(self, event):
        if self.first_frame:
            self.t_start = time.monotonic()
            self.first_frame = False

    def on_timer(self, event):
        pass

    def process_data(self, data: Any) -> None:
        '''define a mapping between the data argument and shader variables'''
        pass

class VisualStimWorker(WorkerNode):

    def __init__(self, stim: VisualStim, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stim = stim
        self.display_process = None

    def run(self) -> None:
        self.stim.initialize()
        # NOTE: this replaces app.run() and gives access to the event loop.
        # The same technique can be used directly with Qt using processEvents instead of exec
        while not self.stop_event.is_set():
            app.process_events()
        self.stim.cleanup()

    def initialize(self) -> None:
        super().initialize()

        # launch main window loop in a separate process 
        self.display_process = Process(target=self.run)
        self.display_process.start()

    def cleanup(self) -> None:
        self.display_process.join()

    def process_data(self, data: Any) -> None:
        return self.stim.process_data(data)
    
    def process_metadata(self, metadata) -> Any:
        pass