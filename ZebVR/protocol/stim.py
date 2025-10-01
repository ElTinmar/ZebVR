from enum import IntEnum

class Stim(IntEnum):

    # visual
    DARK = 0
    BRIGHT = 1
    PHOTOTAXIS = 2
    OMR = 3
    OKR = 4
    LOOMING = 5
    PREY_CAPTURE = 6
    CONCENTRIC_GRATING = 7
    DOT = 8
    IMAGE = 9
    RAMP = 10
    TURING = 11

    # acoustic
    PURE_TONE = 100
    FREQUENCY_RAMP = 101
    WHITE_NOISE = 102
    PINK_NOISE = 103
    BROWN_NOISE = 104
    CLICK_TRAIN = 105
    SILENCE = 106
    AUDIO_FILE = 107

    # daq
    DIGITAL_WRITE = 200
    ANALOG_WRITE = 201
    PWM_WRITE = 202
    DIGITAL_PULSE = 203
    PWM_PULSE = 204
    ANALOG_PULSE = 205

    def __str__(self):
        return self.name
    
VISUAL_STIMS = [s for s in Stim if 0 <= s.value <= 99]
AUDIO_STIMS = [s for s in Stim if 100 <= s.value <= 199]
DAQ_STIMS =  [s for s in Stim if 200 <= s.value <= 299]

class PreyCaptureType(IntEnum):
    RING = 0
    RANDOM_CLOUD = 1 

    def __str__(self) -> str:
        return self.name
    
class RampType(IntEnum):
    LINEAR = 0
    POWER_LAW = 1 # Stevens' law
    LOG = 2 # Fechner's law

    def __str__(self) -> str:
        return self.name

class LoomingType(IntEnum):
    LINEAR_RADIUS = 0
    LINEAR_ANGLE = 1
    CONSTANT_VELOCITY = 2 

    def __str__(self) -> str:
        return self.name
    
class CoordinateSystem(IntEnum):
    BOUNDING_BOX_CENTER = 0
    FISH_CENTERED = 1
    FISH_EGOCENTRIC = 2 

    def __str__(self) -> str:
        return self.name