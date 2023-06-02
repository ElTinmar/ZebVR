from screeninfo import get_monitors
from numpy.typing import NDArray
from psychopy import visual, core
import numpy as np
from typing import Tuple
from core.abstractclasses import Projector  
import time

class PsychoPyProjector(Projector):
    def __init__(self, monitor_id=1) -> None:
        super().__init__()
        
        offset_x = 0
        for id, monitor in enumerate(get_monitors()):
            width = monitor.width
            height = monitor.height
            if id == monitor_id:
                break
            offset_x = offset_x + width

        self.monitor_id = monitor_id
        self.win_width = width
        self.win_height = height
        self.offset_x = offset_x
        
    def init_window(self):
        self.win = visual.Window(
            size=(self.win_width,self.win_height),
            fullscr=True,
            screen = self.monitor_id
        )

    def close_window(self):
        self.win.close()

    def calibration(self, num_pixels = 100) -> None:
        """
        Project a checkerboard on top of a real world checkerboard pattern 
        with known dimensions, correct image distortions and get mm/px.
        (Opt. correct for spatial intensity inhomogeneities: either fit a model
        with a few parameters e.g. a gaussian, or without a model with one 
        parameter for each pixel.)
        """

    def project(self, image: NDArray) -> None:
        """
        Input image to project
        """

        visual.ImageStim(self.win, image)
        self.win.flip()

    def get_resolution(self) -> Tuple[int, int]:
        return (self.win_width, self.win_height)
