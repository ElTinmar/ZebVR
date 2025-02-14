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
    def initialize(self) -> None:
        pass

    @abstractmethod
    def done(self, metadata: Optional[Any]) -> bool:
        pass

class Pause(StopCondition):

    def __init__(self, pause_sec: float = 0) -> None:
        super().__init__()
        self.pause_sec = pause_sec
        self.time_start = None

    def initialize(self) -> None:
        self.time_start = time.perf_counter()

    def done(self, metadata: Optional[Any]) -> bool:
        if (time.perf_counter() - self.time_start) < self.pause_sec:
            return False
        else:
            return True

class SoftwareTrigger(StopCondition):

    def __init__(
            self, 
            polarity = TriggerPolarity.RISING_EDGE,
            debouncer_length: int = 3 
        ) -> None:

        super().__init__()
        self.polarity = polarity
        self.debouncer = Debouncer(debouncer_length)

    def initialize(self) -> None:
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
            trigger_mask: NDArray,
            polarity = TriggerPolarity.RISING_EDGE,
            debouncer_length: int = 3
        ) -> None:

        super().__init__()
        
        self.trigger_mask = trigger_mask
        self.polarity = polarity
        self.debouncer = Debouncer(debouncer_length)

    def initialize(self) -> None:
        pass
    
    # TODO type metadata properly (nested TypedDict?) / maybe send only centroid and not full tracking 
    def done(self, metadata: Optional[Any]) -> bool:
         
        output = False

        if metadata is None:
            return output
        
        fish_centroid = np.zeros((2,), dtype=float)
        
        try:
            tracking = metadata['tracker_metadata']['tracking']

            # TODO choose animal
            k = tracking['animals']['identities'][0]

            if tracking['body'][k] is not None:
                fish_centroid[:] = tracking['body'][k]['centroid_original_space']
            else:
                fish_centroid[:] = tracking['animals']['centroids'][k,:]

        except KeyError:
            return output
        except TypeError:
            return output
        except ValueError:
            return output
        
        x, y = fish_centroid.astype(int)
        triggered = self.trigger_mask[y, x]
        
        transition = self.debouncer.update(triggered)
        if transition.name == self.polarity.name: 
            output = True
        return output