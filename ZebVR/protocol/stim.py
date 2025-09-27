from enum import IntEnum

class Stim(IntEnum):

    # visual
    DARK = 0
    BRIGHT = 1
    PHOTOTAXIS_CLOSED_LOOP = 2
    OMR_CLOSED_LOOP = 3
    OKR_CLOSED_LOOP = 4
    LINEAR_RADIUS_LOOMING_CLOSED_LOOP = 5
    PREY_CAPTURE = 6
    LINEAR_RADIUS_LOOMING = 7
    CONCENTRIC_GRATING = 8
    DOT_CLOSED_LOOP = 9
    DOT = 10
    IMAGE = 11
    RAMP = 12
    PREY_CAPTURE_CLOSED_LOOP = 13
    LINEAR_ANGLE_LOOMING = 14
    LINEAR_ANGLE_LOOMING_CLOSED_LOOP = 15
    CONSTANT_APPROACH_SPEED_LOOMING = 16
    CONSTANT_APPROACH_SPEED_LOOMING_CLOSED_LOOP = 17

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

class RampType(IntEnum):
    LINEAR = 0
    POWER_LAW = 1 # Stevens' law
    LOG = 2 # Fechner's law

    def __str__(self) -> str:
        return self.name
    