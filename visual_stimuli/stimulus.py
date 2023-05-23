from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class Tracking:
    x: float 
    y: float
    theta: float
    eye
    skeleton
    hasEyes: bool = False
    hasTail: bool = False

class Stimulus(ABC):
    """
    Abstract base class defining the interface for writing new visual stimuli
    """
    
    def __init__(self, affine_trans):
        pass

    @abstractmethod
    def create_stim(self):
        """Use the"""
        pass