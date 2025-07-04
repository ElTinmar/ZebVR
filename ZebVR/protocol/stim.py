from enum import IntEnum

class Stim(IntEnum):

    # visual
    DARK = 0
    BRIGHT = 1
    PHOTOTAXIS = 2
    OMR = 3
    OKR = 4
    FOLLOWING_LOOMING = 5
    PREY_CAPTURE = 6
    LOOMING = 7
    CONCENTRIC_GRATING = 8
    FOLLOWING_DOT = 9
    DOT = 10
    IMAGE = 11
    RAMP = 12

    # acoustic
    PURE_TONE = 20
    FREQUENCY_RAMP = 21
    WHITE_NOISE = 22
    PINK_NOISE = 23
    BROWN_NOISE = 24
    CLICK_TRAIN = 25
    SILENCE = 26
    AUDIO_FILE = 27

    # daq
    DIGITAL_OUTPUT = 30
    ANALOG_OUTPUT = 31
    PWM_OUTPUT = 32
    TTL_PULSE = 33
    PWM_PULSE = 34

    def __str__(self):
        return self.name
    

class RampType(IntEnum):
    LINEAR = 0
    POWER_LAW = 1 # Stevens' law
    LOG = 2 # Fechner's law

    def __str__(self) -> str:
        return self.name
    