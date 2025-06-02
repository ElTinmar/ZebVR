from .protocol_item import *
from .stop_condition import *
from .visual import *

PROTOCOL_WIDGETS = {
    'w_bright': (visual.BrightWidget, protocol_item.Stim.Visual.BRIGHT),
    'w_concentric_grating': (visual.ConcentricGratingWidget, protocol_item.Stim.Visual.CONCENTRIC_GRATING),
    'w_dark': (visual.DarkWidget, protocol_item.Stim.Visual.DARK),
    'w_dot': (visual.DotWidget, protocol_item.Stim.Visual.DOT),
    'w_following_dot': (visual.FollowingDotWidget, protocol_item.Stim.Visual.FOLLOWING_DOT),
    'w_looming': (visual.LoomingWidget, protocol_item.Stim.Visual.LOOMING),
    'w_following_looming': (visual.FollowingLoomingWidget, protocol_item.Stim.Visual.FOLLOWING_LOOMING),
    'w_okr': (visual.OKR_Widget, protocol_item.Stim.Visual.OKR),
    'w_omr': (visual.OMR_Widget, protocol_item.Stim.Visual.OMR),
    'w_phototaxis': (visual.PhototaxisWidget, protocol_item.Stim.Visual.PHOTOTAXIS),
    'w_prey_capture': (visual.PreyCaptureWidget, protocol_item.Stim.Visual.PREY_CAPTURE)
}
