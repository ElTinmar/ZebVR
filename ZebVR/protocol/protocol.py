from collections import defaultdict
from typing import Dict, Optional, Tuple, DefaultDict, Any,TypedDict
from abc import ABC, abstractmethod
from enum import IntEnum
import time

class Stim(IntEnum):
    DARK = 0
    BRIGHT = 1
    PHOTOTAXIS = 2
    OMR = 3
    OKR = 4
    LOOMING = 5

    def __str__(self):
        return self.name

class TriggerType(IntEnum):
    SOFTWARE = 0
    TTL = 1

    def __str__(self):
        return self.name

class TriggerPolarity(IntEnum):
    RISING_EDGE = 0
    FALLING_EDGE = 1

    def __str__(self):
        return self.name
    
class ProtocolItem(ABC):

    STIM_SELECT: Optional[int] = None

    def start(self) -> None:
        pass

    @abstractmethod
    def done(self, metadata: Optional[Any]) -> Optional[Tuple[DefaultDict, bool]]:
        pass

    def initialize(self):
        '''Run init steps in target worker process'''
        pass

    def cleanup(self):
        '''Run cleanup steps in target worker process'''
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, d: Dict) -> None:
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict:
        pass

class ProtocolItemPause(ProtocolItem):

    def __init__(self, pause_sec: float) -> None:
        super().__init__()
        self.pause_sec = pause_sec
        self.time_start = None

    def start(self) -> None:
        self.time_start = time.perf_counter()

    def done(self, metadata: Optional[Any]) -> Tuple[Any, bool]:
        if (time.perf_counter() - self.time_start) < self.pause_sec:
            return None, False
        else:
            return None, True

    @classmethod
    def from_dict(cls, d: Dict):
        return cls(pause_sec = d['pause_sec'])

    def to_dict(self) -> Dict:
        res = {}
        res['type'] = 'pause'
        res['pause_sec'] = self.pause_sec
        return res

# TODO: implement trigger
# Example of trigger: 
#       - fish coordinates in specific region
#       - keypress
#       - TTL signal on DAQ

class MetadataTrigger(TypedDict):
    trigger: int # either 1 or 0

class ProtocolItemSoftwareTrigger(ProtocolItem):

    def __init__(
            self, 
            polarity = TriggerPolarity.RISING_EDGE,
        ) -> None:

        super().__init__()
        self.polarity = polarity
        self.current_value = 0

    def done(self, metadata: Optional[MetadataTrigger]) -> Tuple[Any, bool]:

        try:
            value = metadata['trigger'] 
            delta = value - self.current_value
            self.current_value = value

            if self.polarity == TriggerPolarity.RISING_EDGE:
                return (None, True) if delta > 0 else (None, False)
            
            elif self.polarity == TriggerPolarity.FALLING_EDGE: 
                return (None, True) if delta < 0 else (None, False)
            
        except (TypeError, KeyError): 
            return None, False

    @classmethod
    def from_dict(cls, d: Dict):
        return cls()

    def to_dict(self) -> Dict:
        return {}

"""
class ProtocolItemTTLTrigger(ProtocolItem):

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

    def done(self) -> None:
        self.daq.wait_trigger()
        return None

    @classmethod
    def from_dict(cls, d: Dict):
        return cls()

    def to_dict(self) -> Dict:
        return {}
"""

# TODO 
"""
class ProtocolItemSound(ProtocolItem):

    STIM_SELECT: Optional[int] = None

    def __init__(self, wavfile: str) -> None:
       super().__init__()
       self.wavfile = wavfile

    def done(self) -> Optional[DefaultDict]:
        command = defaultdict(float, {
            'stim_select': self.SOUND,
            'wavfile': self.wavfile,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'looming_center_mm': (0, 0)
        })
        return command 

    def initialize(self):
        '''Run init steps in target worker process'''
        pass

    def cleanup(self):
        '''Run cleanup steps in target worker process'''
        pass

    @classmethod
    def from_dict(cls, d: Dict) -> None:
        pass
    
    def to_dict(self) -> Dict:
        pass

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

    def start(self) -> None:
        pass

    def done(self, metadata: Optional[Any]) -> Tuple[Any, bool]:

        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'phototaxis_polarity': self.phototaxis_polarity,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'looming_center_mm': (0, 0)
        })
        return command, True
    
    @classmethod
    def from_dict(cls, d: Dict) -> None:
        return cls(
            phototaxis_polarity = d['phototaxis_polarity'],
            foreground_color = d['foreground_color'],
            background_color = d['background_color']
        )

    def to_dict(self) -> Dict:
        res = {}
        res['type'] = 'phototaxis'
        res['phototaxis_polarity'] = self.phototaxis_polarity
        res['foreground_color'] = self.foreground_color
        res['background_color'] = self.background_color
        return res
    
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

    def start(self) -> None:
        pass

    def done(self, metadata: Optional[Any]) -> Tuple[Any, bool]:
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'okr_spatial_frequency_deg': self.okr_spatial_frequency_deg,
            'okr_speed_deg_per_sec': self.okr_speed_deg_per_sec,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'looming_center_mm': (0, 0)
        })
        return command, True 

    @classmethod
    def from_dict(cls, d: Dict) -> None:
        return cls(
            okr_spatial_frequency_deg = d['okr_spatial_frequency_deg'],
            okr_speed_deg_per_sec = d['okr_speed_deg_per_sec'],
            foreground_color = d['foreground_color'],
            background_color = d['background_color']
        )

    def to_dict(self) -> Dict:
        res = {}
        res['type'] = 'OKR'
        res['okr_spatial_frequency_deg'] = self.okr_spatial_frequency_deg
        res['okr_speed_deg_per_sec'] = self.okr_speed_deg_per_sec
        res['foreground_color'] = self.foreground_color
        res['background_color'] = self.background_color
        return res
    
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
    
    def start(self) -> None:
        pass

    def done(self, metadata: Optional[Any]) -> Tuple[Any, bool]:
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'omr_spatial_period_mm': self.omr_spatial_period_mm,
            'omr_angle_deg': self.omr_angle_deg,
            'omr_speed_mm_per_sec': self.omr_speed_mm_per_sec,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'looming_center_mm': (0, 0)
        })
        return command, True 

    @classmethod
    def from_dict(cls, d: Dict) -> None:
        return cls(
            omr_spatial_period_mm = d['omr_spatial_period_mm'],
            omr_angle_deg = d['omr_angle_deg'],
            omr_speed_mm_per_sec = d['omr_speed_mm_per_sec'],
            foreground_color = d['foreground_color'],
            background_color = d['background_color']
        )

    def to_dict(self) -> Dict:
        res = {}
        res['type'] = 'OMR'
        res['omr_spatial_period_mm'] = self.omr_spatial_period_mm
        res['omr_angle_deg'] = self.omr_angle_deg
        res['omr_speed_mm_per_sec'] = self.omr_speed_mm_per_sec
        res['foreground_color'] = self.foreground_color
        res['background_color'] = self.background_color
        return res
    
class ProtocolItemDark(ProtocolItem):

    STIM_SELECT = Stim.DARK

    def __init__(
            self,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float]
        ) -> None:

        super().__init__()
        self.foreground_color = foreground_color
        self.background_color = background_color 

    def start(self) -> None:
        pass

    def done(self, metadata: Optional[Any]) -> Tuple[Any, bool]:
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'looming_center_mm': (0, 0)
        })
        return command, True 

    @classmethod
    def from_dict(cls, d: Dict) -> None:
        return cls(
            foreground_color = d['foreground_color'],
            background_color = d['background_color']
        )

    def to_dict(self) -> Dict:
        res = {}
        res['type'] = 'dark'
        res['foreground_color'] = self.foreground_color
        res['background_color'] = self.background_color
        return res

class ProtocolItemBright(ProtocolItem):

    STIM_SELECT = Stim.BRIGHT

    def __init__(
            self, 
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float]
        ) -> None:

        super().__init__()
        self.foreground_color = foreground_color 
        self.background_color = background_color 

    def start(self) -> None:
        pass

    def done(self, metadata: Optional[Any]) -> Tuple[Any, bool]:
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'looming_center_mm': (0, 0)
        })
        return command, True 
    
    @classmethod
    def from_dict(cls, d: Dict) -> None:
        return cls(
            foreground_color = d['foreground_color'],
            background_color = d['background_color']
        )

    def to_dict(self) -> Dict:
        res = {}
        res['type'] = 'bright'
        res['foreground_color'] = self.foreground_color
        res['background_color'] = self.background_color
        return res

class ProtocolItemLooming(ProtocolItem):

    STIM_SELECT = Stim.LOOMING

    def __init__(
            self, 
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            looming_center_mm: Tuple[float, float],
            looming_period_sec: float,
            looming_expansion_time_sec: float,
            looming_expansion_speed_mm_per_sec: float   
        ) -> None:

        super().__init__()
        self.foreground_color = foreground_color 
        self.background_color = background_color
        self.looming_center_mm = looming_center_mm
        self.looming_period_sec = looming_period_sec 
        self.looming_expansion_time_sec = looming_expansion_time_sec
        self.looming_expansion_speed_mm_per_sec = looming_expansion_speed_mm_per_sec

    def start(self) -> None:
        pass

    def done(self, metadata: Optional[Any]) -> Tuple[Any, bool]:
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'looming_center_mm': self.looming_center_mm,
            'looming_period_sec': self.looming_period_sec,
            'looming_expansion_time_sec': self.looming_expansion_time_sec,
            'looming_expansion_speed_mm_per_sec': self.looming_expansion_speed_mm_per_sec,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
        })
        return command, True 

    @classmethod
    def from_dict(cls, d: Dict) -> None:
        return cls(
            foreground_color = d['foreground_color'],
            background_color = d['background_color'],
            looming_center_mm = d['looming_center_mm'],
            looming_period_sec = d['looming_period_sec'],
            looming_expansion_time_sec = d['looming_expansion_time_sec'],
            looming_expansion_speed_mm_per_sec = d['looming_expansion_speed_mm_per_sec']
        )

    def to_dict(self) -> Dict:
        res = {}
        res['type'] = 'looming'
        res['looming_center_mm'] = self.looming_center_mm
        res['looming_period_sec'] = self.looming_period_sec
        res['looming_expansion_time_sec'] = self.looming_expansion_time_sec
        res['looming_expansion_speed_mm_per_sec'] = self.looming_expansion_speed_mm_per_sec
        res['foreground_color'] = self.foreground_color
        res['background_color'] = self.background_color
        return res