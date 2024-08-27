from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional, Tuple
import time
from ZebVR.widgets import StimWidget # Should I do relative imports instead?

from PyQt5.QtWidgets import QApplication

class StimGUI(WorkerNode):

    def __init__(
            self, 
            phototaxis_polarity: int = 1,
            omr_spatial_period_mm: float = 5,
            omr_angle_deg: float = 0,
            omr_speed_mm_per_sec: float = 10,
            okr_spatial_frequency_deg: float = 20,
            okr_speed_deg_per_sec: float = 36,
            looming_center_mm: Tuple = (15,15),
            looming_period_sec: float = 30,
            looming_expansion_time_sec: float = 10,
            looming_expansion_speed_mm_per_sec: float = 10,
            foreground_color: Tuple = (0.2, 0.2, 0.2, 1.0),
            background_color: Tuple = (0.0, 0.0, 0.0, 1.0),
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)

        self.phototaxis_polarity = phototaxis_polarity
        self.omr_spatial_period_mm = omr_spatial_period_mm
        self.omr_angle_deg = omr_angle_deg
        self.omr_speed_mm_per_sec = omr_speed_mm_per_sec
        self.okr_spatial_frequency_deg = okr_spatial_frequency_deg
        self.okr_speed_deg_per_sec = okr_speed_deg_per_sec
        self.looming_center_mm = looming_center_mm
        self.looming_period_sec = looming_period_sec
        self.looming_expansion_time_sec = looming_expansion_time_sec
        self.looming_expansion_speed_mm_per_sec = looming_expansion_speed_mm_per_sec
        self.foreground_color = foreground_color
        self.background_color = background_color

    def initialize(self) -> None:
        super().initialize()
        self.app = QApplication([])
        self.window = StimWidget(
            phototaxis_polarity=self.phototaxis_polarity,
            omr_spatial_period_mm=self.omr_spatial_period_mm,
            omr_angle_deg=self.omr_angle_deg,
            omr_speed_mm_per_sec=self.omr_speed_mm_per_sec,
            okr_spatial_frequency_deg=self.okr_spatial_frequency_deg,
            okr_speed_deg_per_sec=self.okr_speed_deg_per_sec,
            looming_center_mm=self.looming_center_mm,
            looming_period_sec=self.looming_period_sec,
            looming_expansion_time_sec=self.looming_expansion_time_sec,
            looming_expansion_speed_mm_per_sec=self.looming_expansion_speed_mm_per_sec,
            foreground_color=self.foreground_color,
            background_color=self.background_color
        )
        self.window.show()
    
    def process_data(self, data: None) -> NDArray:
        self.app.processEvents()
        self.app.sendPostedEvents()
        time.sleep(0.01)

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        # send only one message when things are changed
        if self.window.is_updated():
            res = {}
            res['visual_stim_control'] = self.window.get_state()
            self.window.set_updated(False)
            return res       
        else:
            return None
        