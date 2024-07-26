from dagline import WorkerNode
import time
from numpy.typing import NDArray
from typing import Dict, Optional, Any, Deque, Tuple, DefaultDict
from abc import ABC, abstractmethod
from enum import IntEnum
from collections import defaultdict

#TODO make phototaxis polarity an IntEnum :
#class PhototaxisPolarity(IntEnum):
#    DARK_RIGHT = 1
#    DARK_LEFT = -1

class Stim(IntEnum):
    DARK = 0
    BRIGHT = 1
    PHOTOTAXIS = 2
    OMR = 3
    OKR = 4
    LOOMING = 5

class ProtocolItem(ABC):

    STIM_SELECT: Optional[int] = None

    @abstractmethod
    def run(self) -> Optional[DefaultDict]:
        pass

    def initialize(self):
        '''Run init steps in target worker process'''
        pass

    def cleanup(self):
        '''Run cleanup steps in target worker process'''
        pass

# TODO implement this. maybe use keyboard module
'''
class ProtocolItemWaitKeyPress(ProtocolItem):

    def run(self) -> None:
        input('press Enter:') # input does not work in child process
        return None
'''

class ProtocolItemPause(ProtocolItem):

    def __init__(self, pause_sec: float) -> None:
        super().__init__()
        self.pause_sec = pause_sec

    def run(self) -> None:
        time.sleep(self.pause_sec)
        return None

# TODO: implement trigger
"""
class ProtocolItemTrigger(ProtocolItem):

   def __init__(self, port: int) -> None:
       '''give info necessary to create DAQ object'''
       super().__init__()
       self.port = port

   def initialize(self):
        '''create DAQ object'''
        super().initialize()
        self.daq.open(port=self.port)
   
   def cleanup(self):
        '''create DAQ object'''
        super().cleanup()
        self.daq.close()
   
   def run(self) -> None:
       self.daq.wait_trigger()
       return None
"""

class ProtocolItemPhototaxis(ProtocolItem):

    STIM_SELECT = Stim.PHOTOTAXIS

    def __init__(
            self, 
            phototaxis_polarity: int,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float]
        ) -> None:

        super().__init__()
        self.phototaxis_polarity = phototaxis_polarity
        self.foreground_color = foreground_color
        self.background_color = background_color 

    def run(self) -> DefaultDict:
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'phototaxis_polarity': self.phototaxis_polarity,
            'foreground_color_R': self.foreground_color[0], 
            'foreground_color_G': self.foreground_color[1],
            'foreground_color_B': self.foreground_color[2],
            'foreground_color_A': self.foreground_color[3],
            'background_color_R': self.background_color[0],
            'background_color_G': self.background_color[1],
            'background_color_B': self.background_color[2],
            'background_color_A': self.background_color[3]
        })
        return command 
    
class ProtocolItemOKR(ProtocolItem):

    STIM_SELECT = Stim.OKR

    def __init__(
            self, 
            okr_spatial_frequency_deg: float,
            okr_speed_deg_per_sec: float,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float]
        ) -> None:

        super().__init__()
        self.okr_spatial_frequency_deg = okr_spatial_frequency_deg
        self.okr_speed_deg_per_sec = okr_speed_deg_per_sec
        self.foreground_color = foreground_color
        self.background_color = background_color 

    def run(self) -> DefaultDict:
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'okr_spatial_frequency_deg': self.okr_spatial_frequency_deg,
            'okr_speed_deg_per_sec': self.okr_speed_deg_per_sec,
            'foreground_color_R': self.foreground_color[0], 
            'foreground_color_G': self.foreground_color[1],
            'foreground_color_B': self.foreground_color[2],
            'foreground_color_A': self.foreground_color[3],
            'background_color_R': self.background_color[0],
            'background_color_G': self.background_color[1],
            'background_color_B': self.background_color[2],
            'background_color_A': self.background_color[3]
        })
        return command 

class ProtocolItemOMR(ProtocolItem):
    
    STIM_SELECT = Stim.OMR
    
    def __init__(
            self, 
            omr_spatial_period_mm: float,
            omr_angle_deg: float,
            omr_speed_mm_per_sec: float,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float]
        ) -> None:

        super().__init__()
        self.omr_spatial_period_mm = omr_spatial_period_mm
        self.omr_angle_deg = omr_angle_deg
        self.omr_speed_mm_per_sec = omr_speed_mm_per_sec
        self.foreground_color = foreground_color
        self.background_color = background_color 

    def run(self) -> DefaultDict:
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'omr_spatial_period_mm': self.omr_spatial_period_mm,
            'omr_angle_deg': self.omr_angle_deg,
            'omr_speed_mm_per_sec': self.omr_speed_mm_per_sec,
            'foreground_color_R': self.foreground_color[0], 
            'foreground_color_G': self.foreground_color[1],
            'foreground_color_B': self.foreground_color[2],
            'foreground_color_A': self.foreground_color[3],
            'background_color_R': self.background_color[0],
            'background_color_G': self.background_color[1],
            'background_color_B': self.background_color[2],
            'background_color_A': self.background_color[3]
        })
        return command 

class ProtocolItemDark(ProtocolItem):

    STIM_SELECT = Stim.DARK

    def __init__(
            self, 
            background_color: Tuple[float, float, float, float]
        ) -> None:

        super().__init__()
        self.background_color = background_color 

    def run(self) -> DefaultDict:
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'background_color_R': self.background_color[0],
            'background_color_G': self.background_color[1],
            'background_color_B': self.background_color[2],
            'background_color_A': self.background_color[3]
        })
        return command 

class ProtocolItemBright(ProtocolItem):

    STIM_SELECT = Stim.BRIGHT

    def __init__(
            self, 
            foreground_color: Tuple[float, float, float, float]
        ) -> None:

        super().__init__()
        self.foreground_color = foreground_color 

    def run(self) -> DefaultDict:
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'foreground_color_R': self.foreground_color[0],
            'foreground_color_G': self.foreground_color[1],
            'foreground_color_B': self.foreground_color[2],
            'foreground_color_A': self.foreground_color[3]
        })
        return command 

class ProtocolItemLooming(ProtocolItem):

    STIM_SELECT = Stim.LOOMING

    def __init__(
            self, 
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            looming_center_mm_x: float,
            looming_center_mm_y: float,
            looming_period_sec: float,
            looming_expansion_time_sec: float,
            looming_expansion_speed_mm_per_sec: float   
        ) -> None:

        super().__init__()
        self.foreground_color = foreground_color 
        self.background_color = background_color
        self.looming_center_mm_x = looming_center_mm_x
        self.looming_center_mm_y = looming_center_mm_y
        self.looming_period_sec = looming_period_sec 
        self.looming_expansion_time_sec = looming_expansion_time_sec
        self.looming_expansion_speed_mm_per_sec = looming_expansion_speed_mm_per_sec

    def run(self) -> DefaultDict:
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'looming_center_mm_x': self.looming_center_mm_x,
            'looming_center_mm_y': self.looming_center_mm_y,
            'looming_period_sec': self.looming_period_sec,
            'looming_expansion_time_sec': self.looming_expansion_time_sec,
            'looming_expansion_speed_mm_per_sec': self.looming_expansion_speed_mm_per_sec,
            'foreground_color_R': self.foreground_color[0],
            'foreground_color_G': self.foreground_color[1],
            'foreground_color_B': self.foreground_color[2],
            'foreground_color_A': self.foreground_color[3],
            'background_color_R': self.background_color[0],
            'background_color_G': self.background_color[1],
            'background_color_B': self.background_color[2],
            'background_color_A': self.background_color[3]
        })
        return command 
        
class Protocol(WorkerNode):

    def __init__(
            self, 
            protocol: Optional[Deque[ProtocolItem]] = None,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.protocol = protocol

    def set_protocol(self, protocol: Deque[ProtocolItem]) -> None:
        self.protocol = protocol

    def initialize(self) -> None:
        super().initialize()
        for protocol_item in self.protocol:
            protocol_item.initialize()

    def cleanup(self) -> None:
        super().cleanup()
        for protocol_item in self.protocol:
            protocol_item.cleanup()

    def process_data(self, data: Any) -> NDArray:
        pass

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:    
        
        try:
            item = self.protocol.popleft()
        except IndexError:
            print('Protocol finished, stopping sequencer')
            self.stop_event.set()
            return None

        # item.run() either waits and eventually returns None, 
        # or returns a Dict with command dictionnary 
        command = item.run()

        if command is None:
            return 
        
        res = {}
        res['visual_stim_control'] = command
        return res