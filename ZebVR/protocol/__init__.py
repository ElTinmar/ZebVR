from .protocol_item import *
from .stop_condition import *
from .visual import *

PROTOCOL_WIDGETS = {
    'bright': (visual.BrightWidget, protocol_item.Stim.Visual.BRIGHT),
    'concentric_grating': (visual.ConcentricGratingWidget, protocol_item.Stim.Visual.CONCENTRIC_GRATING),
    'dark': (visual.DarkWidget, protocol_item.Stim.Visual.DARK),
    'dot': (visual.DotWidget, protocol_item.Stim.Visual.DOT),
    'following_dot': (visual.FollowingDotWidget, protocol_item.Stim.Visual.FOLLOWING_DOT),
    'looming': (visual.LoomingWidget, protocol_item.Stim.Visual.LOOMING),
    'following_looming': (visual.FollowingLoomingWidget, protocol_item.Stim.Visual.FOLLOWING_LOOMING),
    'okr': (visual.OKR_Widget, protocol_item.Stim.Visual.OKR),
    'omr': (visual.OMR_Widget, protocol_item.Stim.Visual.OMR),
    'phototaxis': (visual.PhototaxisWidget, protocol_item.Stim.Visual.PHOTOTAXIS),
    'prey_capture': (visual.PreyCaptureWidget, protocol_item.Stim.Visual.PREY_CAPTURE)
}
