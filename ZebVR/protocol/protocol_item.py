from collections import defaultdict
from typing import Optional, Tuple, DefaultDict, Any
from abc import ABC
from enum import IntEnum
from .stop_condition import StopCondition, Pause

class Stim:
    class Visual(IntEnum):
        DARK = 0
        BRIGHT = 1
        PHOTOTAXIS = 2
        OMR = 3
        OKR = 4
        LOOMING = 5
        PREY_CAPTURE = 6

        def __str__(self):
            return self.name
    
    class Acoustic(IntEnum):
        PURE_TONE = 0
        WHITE_NOISE = 1

        def __str__(self):
            return self.name
        
class ProtocolItem(ABC):

    STIM_SELECT: Optional[int] = None

    def __init__(self, stop_condition: StopCondition = Pause()):
        self.stop_condition = stop_condition

    def start(self) -> Optional[DefaultDict]:
        self.stop_condition.start()

    def done(self, metadata: Optional[Any]) -> bool:
        return self.stop_condition.done(metadata)

    def initialize(self):
        '''Run init steps in target worker process'''
        pass

    def cleanup(self):
        '''Run cleanup steps in target worker process'''
        pass

    def set_stop_condition(self, stop_condition: StopCondition):
        self.stop_condition = stop_condition

class Phototaxis(ProtocolItem):

    STIM_SELECT = Stim.Visual.PHOTOTAXIS

    def __init__(
            self, 
            phototaxis_polarity: int,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.phototaxis_polarity = phototaxis_polarity
        self.foreground_color = foreground_color
        self.background_color = background_color 

    def start(self) -> DefaultDict:

        super().start()

        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'phototaxis_polarity': self.phototaxis_polarity,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'looming_center_mm': (0, 0)
        })
        return command
    
class OKR(ProtocolItem):

    STIM_SELECT = Stim.Visual.OKR

    def __init__(
            self, 
            okr_spatial_frequency_deg: float,
            okr_speed_deg_per_sec: float,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.okr_spatial_frequency_deg = okr_spatial_frequency_deg
        self.okr_speed_deg_per_sec = okr_speed_deg_per_sec
        self.foreground_color = foreground_color
        self.background_color = background_color 

    def start(self) -> DefaultDict:

        super().start()

        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'okr_spatial_frequency_deg': self.okr_spatial_frequency_deg,
            'okr_speed_deg_per_sec': self.okr_speed_deg_per_sec,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'looming_center_mm': (0, 0)
        })
        return command

class OMR(ProtocolItem):
    
    STIM_SELECT = Stim.Visual.OMR
    
    def __init__(
            self, 
            omr_spatial_period_mm: float,
            omr_angle_deg: float,
            omr_speed_mm_per_sec: float,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.omr_spatial_period_mm = omr_spatial_period_mm
        self.omr_angle_deg = omr_angle_deg
        self.omr_speed_mm_per_sec = omr_speed_mm_per_sec
        self.foreground_color = foreground_color
        self.background_color = background_color 
    
    def start(self) -> DefaultDict:

        super().start()

        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'omr_spatial_period_mm': self.omr_spatial_period_mm,
            'omr_angle_deg': self.omr_angle_deg,
            'omr_speed_mm_per_sec': self.omr_speed_mm_per_sec,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'looming_center_mm': (0, 0)
        })
        return command

class Dark(ProtocolItem):

    STIM_SELECT = Stim.Visual.DARK

    def __init__(
            self,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.foreground_color = foreground_color
        self.background_color = background_color 

    def start(self) -> DefaultDict:

        super().start()
        
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'looming_center_mm': (0, 0)
        })
        return command

class Bright(ProtocolItem):

    STIM_SELECT = Stim.Visual.BRIGHT

    def __init__(
            self, 
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.foreground_color = foreground_color 
        self.background_color = background_color 

    def start(self) -> DefaultDict:

        super().start()
        
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'looming_center_mm': (0, 0)
        })
        return command

class Looming(ProtocolItem):

    STIM_SELECT = Stim.Visual.LOOMING

    def __init__(
            self, 
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            looming_center_mm: Tuple[float, float],
            looming_period_sec: float,
            looming_expansion_time_sec: float,
            looming_expansion_speed_mm_per_sec: float,
            *args,
            **kwargs   
        ) -> None:

        super().__init__(*args, **kwargs)
        self.foreground_color = foreground_color 
        self.background_color = background_color
        self.looming_center_mm = looming_center_mm
        self.looming_period_sec = looming_period_sec 
        self.looming_expansion_time_sec = looming_expansion_time_sec
        self.looming_expansion_speed_mm_per_sec = looming_expansion_speed_mm_per_sec

    def start(self) -> DefaultDict:

        super().start()
        
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'looming_center_mm': self.looming_center_mm,
            'looming_period_sec': self.looming_period_sec,
            'looming_expansion_time_sec': self.looming_expansion_time_sec,
            'looming_expansion_speed_mm_per_sec': self.looming_expansion_speed_mm_per_sec,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
        })
        return command 

class PreyCapture(ProtocolItem):

    STIM_SELECT = Stim.Visual.PREY_CAPTURE

    def __init__(
            self, 
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            n_preys: int = 50,
            prey_speed_mm_s: float = 0.75,
            prey_radius_mm: float = 0.25,
            *args,
            **kwargs   
        ) -> None:

        super().__init__(*args, **kwargs)
        self.foreground_color = foreground_color 
        self.background_color = background_color
        self.n_preys = n_preys
        self.prey_speed_mm_s = prey_speed_mm_s 
        self.prey_radius_mm = prey_radius_mm

    def start(self) -> DefaultDict:

        super().start()
        
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'looming_center_mm': (0, 0),
            'n_preys': self.n_preys,
            'prey_speed_mm_s': self.prey_speed_mm_s,
            'prey_radius_mm': self.prey_radius_mm,
        })
        return command 
    
class PureTone(ProtocolItem):
    pass

class WhiteNoise(ProtocolItem):
    pass
