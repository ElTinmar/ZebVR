from .stim import *
from .protocol_item import *
from .visual_protocol_item import *
from .audio_protocol_item import *
from .daq_protocol_item import *
from .stop_condition import *
from .visual import *
from .acoustic import *
from .default import *

PROTOCOL_WIDGETS = [
    (visual.DarkWidget, Stim.DARK),
    (visual.BrightWidget, Stim.BRIGHT),
    (visual.PhototaxisWidget, Stim.PHOTOTAXIS),
    (visual.OKR_Widget, Stim.OKR),
    (visual.OMR_Widget, Stim.OMR),
    (visual.DotWidget, Stim.DOT),
    (visual.FollowingDotWidget, Stim.FOLLOWING_DOT),
    (visual.LoomingWidget, Stim.LOOMING),
    (visual.FollowingLoomingWidget, Stim.FOLLOWING_LOOMING),
    (visual.PreyCaptureWidget, Stim.PREY_CAPTURE),
    (visual.ConcentricGratingWidget, Stim.CONCENTRIC_GRATING),
    (visual.RampWidget, Stim.RAMP),
    (visual.ImageWidget, Stim.IMAGE),
    (acoustic.PureToneWidget, Stim.PURE_TONE),
    (acoustic.WhiteNoiseWidget, Stim.WHITE_NOISE),
    (acoustic.PinkNoiseWidget, Stim.PINK_NOISE),
    (acoustic.BrownNoiseWidget, Stim.BROWN_NOISE),
    (acoustic.ClickTrainWidget, Stim.CLICK_TRAIN),
    (acoustic.FrequencyRampWidget, Stim.FREQUENCY_RAMP),
    (acoustic.SilenceWidget, Stim.SILENCE),
    (acoustic.AudioFileWidget, Stim.AUDIO_FILE),
]
PROTOCOL_WIDGETS.sort(key = lambda x: x[1])