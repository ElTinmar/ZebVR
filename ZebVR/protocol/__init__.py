from .protocol_item import *
from .stop_condition import *
from .visual import *
from .default import *

PROTOCOL_WIDGETS = [
    (visual.DarkWidget, protocol_item.Stim.DARK),
    (visual.BrightWidget, protocol_item.Stim.BRIGHT),
    (visual.PhototaxisWidget, protocol_item.Stim.PHOTOTAXIS),
    (visual.OKR_Widget, protocol_item.Stim.OKR),
    (visual.OMR_Widget, protocol_item.Stim.OMR),
    (visual.DotWidget, protocol_item.Stim.DOT),
    (visual.FollowingDotWidget, protocol_item.Stim.FOLLOWING_DOT),
    (visual.LoomingWidget, protocol_item.Stim.LOOMING),
    (visual.FollowingLoomingWidget, protocol_item.Stim.FOLLOWING_LOOMING),
    (visual.PreyCaptureWidget, protocol_item.Stim.PREY_CAPTURE),
    (visual.ConcentricGratingWidget, protocol_item.Stim.CONCENTRIC_GRATING),
    (visual.BrightnessRampWidget, protocol_item.Stim.BRIGHTNESS_RAMP),
    (visual.ImageWidget, protocol_item.Stim.IMAGE),
]
PROTOCOL_WIDGETS.sort(key = lambda x: x[1])