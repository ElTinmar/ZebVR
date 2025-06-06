from vispy import app, gloo
from typing import Tuple, Any
from dagline import WorkerNode
from multiprocessing import Process
from numpy.typing import NDArray
import numpy as np 
from multiprocessing import Event
from geometry import AffineTransform2D

class VisualStim(app.Canvas):

    def __init__(
            self, 
            vertex_shader: str, 
            fragment_shader: str,
            window_size: Tuple[int, int],
            window_position: Tuple[int, int],
            camera_resolution: Tuple[int, int],
            pix_per_mm: float,
            window_decoration: bool = False,
            transformation_matrix: AffineTransform2D = AffineTransform2D.identity(),
            pixel_scaling: Tuple[float, float] = (1.0,1.0),
            vsync: bool = False,
            fullscreen: bool = True,
        ) -> None:
            
            self.vertex_shader = vertex_shader
            self.fragment_shader = fragment_shader
            self.window_size = window_size
            self.window_position = window_position
            self.window_decoration = window_decoration 
            self.camera_resolution = camera_resolution
            self.transformation_matrix = transformation_matrix
            self.pixel_scaling = pixel_scaling
            self.vsync = vsync
            self.pix_per_mm = pix_per_mm
            self.use_fullscreen = fullscreen
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

        self.program = gloo.Program(self.vertex_shader, self.fragment_shader)

        # set attributes, these must be present in the vertex shader
        self.program['a_position'] = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
        self.program['u_pixel_scaling'] = self.pixel_scaling
        self.program['u_cam_to_proj'] = self.transformation_matrix.T
        self.program['u_proj_to_cam'] = self.transformation_matrix.inv().T
        self.program['u_pix_per_mm'] = self.pix_per_mm
        self.program['u_pix_per_mm_proj'] = self.transformation_matrix.transform_vectors([self.pix_per_mm, self.pix_per_mm])
        self.program['u_proj_resolution'] = self.window_size
        self.program['u_cam_resolution'] = self.camera_resolution
        
        #NOTE don't forget to call self.initialized.set() in subclass

    def cleanup(self):
        self.initialized.clear()
            
    def on_draw(self, event):
        pass

    def on_timer(self, event):
        pass

    def process_data(self, data: Any) -> None:
        '''define a mapping between the data argument and shader variables'''
        pass

    def process_metadata(self, metadata) -> None:
        pass
    
class VisualStimWorker(WorkerNode):

    def __init__(self, stim: VisualStim, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stim = stim
        self.display_process = None

    def run(self) -> None:
        self.stim.initialize()
        # TODO set flag here
        while not self.stop_event.is_set():
            app.process_events()
        self.stim.cleanup()
        app.quit()

    def set_filename(self, filename:str):
        self.stim.set_filename(filename)

    def initialize(self) -> None:
        super().initialize()
        # launch main window loop in a separate process 
        self.display_process = Process(target=self.run)
        self.display_process.start()
        self.stim.initialized.wait()

    def cleanup(self) -> None:
        super().cleanup()
        self.display_process.join()

    def process_data(self, data: Any) -> None:
        return self.stim.process_data(data)
    
    def process_metadata(self, metadata) -> Any:
        return self.stim.process_metadata(metadata)