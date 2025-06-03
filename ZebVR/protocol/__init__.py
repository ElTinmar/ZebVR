from .protocol_item import *
from .stop_condition import *
from .visual import *
from .default import *

PROTOCOL_WIDGETS = [
    (visual.DarkWidget, protocol_item.Stim.Visual.DARK),
    (visual.BrightWidget, protocol_item.Stim.Visual.BRIGHT),
    (visual.PhototaxisWidget, protocol_item.Stim.Visual.PHOTOTAXIS),
    (visual.OKR_Widget, protocol_item.Stim.Visual.OKR),
    (visual.OMR_Widget, protocol_item.Stim.Visual.OMR),
    (visual.DotWidget, protocol_item.Stim.Visual.DOT),
    (visual.FollowingDotWidget, protocol_item.Stim.Visual.FOLLOWING_DOT),
    (visual.LoomingWidget, protocol_item.Stim.Visual.LOOMING),
    (visual.FollowingLoomingWidget, protocol_item.Stim.Visual.FOLLOWING_LOOMING),
    (visual.PreyCaptureWidget, protocol_item.Stim.Visual.PREY_CAPTURE),
    (visual.ConcentricGratingWidget, protocol_item.Stim.Visual.CONCENTRIC_GRATING),
    (visual.BrightnessRampWidget, protocol_item.Stim.Visual.BRIGHTNESS_RAMP),
    (visual.ImageWidget, protocol_item.Stim.Visual.IMAGE),
]
PROTOCOL_WIDGETS.sort(key = lambda x: x[1])