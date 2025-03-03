from typing import Optional, Any, TypedDict
from abc import ABC, abstractmethod
from enum import IntEnum
import time
import numpy as np
from numpy.typing import NDArray
from .debouncer import Debouncer

class StopPolicy(IntEnum):
    PAUSE = 0
    TRIGGER = 1

    def __str__(self):
        return self.name

class TriggerType(IntEnum):
    SOFTWARE = 0
    TTL = 1
    TRACKING = 2

    def __str__(self):
        return self.name

class TriggerPolarity(IntEnum):
    RISING_EDGE = 0
    FALLING_EDGE = 1

    def __str__(self):
        return self.name

class TriggerDict(TypedDict):
    trigger: int 

class StopCondition(ABC):

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def done(self, metadata: Optional[Any]) -> bool:
        pass

class Pause(StopCondition):

    def __init__(self, pause_sec: float = 0) -> None:
        super().__init__()
        self.pause_sec = pause_sec
        self.time_start = None

    def start(self) -> None:
        self.time_start = time.perf_counter()

    def done(self, metadata: Optional[Any]) -> bool:
        return (time.perf_counter() - self.time_start) >= self.pause_sec

class TTLTrigger(StopCondition):
    pass

class SoftwareTrigger(StopCondition):

    def __init__(
            self, 
            debouncer: Debouncer,
            polarity: TriggerPolarity = TriggerPolarity.RISING_EDGE,
        ) -> None:

        super().__init__()
        self.polarity = polarity
        self.debouncer = debouncer

    def start(self) -> None:
        pass

    def done(self, metadata: Optional[Any]) -> bool:

        output = False

        if metadata is None:
            return output

        try:
            value = metadata['trigger']
        except KeyError: 
            return output
        
        if value is None:
            return output
        
        transition = self.debouncer.update(value)
        if transition.name == self.polarity.name: 
            output = True
        return output

class TrackingTrigger(StopCondition):

    def __init__(
            self, 
            mask_file: str,
            debouncer = Debouncer,
            polarity: TriggerPolarity = TriggerPolarity.RISING_EDGE,
        ) -> None:

        super().__init__()

        self.mask_file = mask_file
        self.mask = np.load(mask_file)
        self.polarity = polarity
        self.debouncer = debouncer

    def start(self) -> None:
        pass
    
    def done(self, metadata: Optional[Any]) -> bool:

        output = False

        if metadata is None:
            return output
        
        try:
            x, y = metadata['tracker_metadata']
            triggered = self.mask[y, x]
        except:
            return output
            
        transition = self.debouncer.update(triggered)
        if transition.name == self.polarity.name: 
            output = True
        return output