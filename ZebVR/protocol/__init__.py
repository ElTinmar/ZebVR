from .protocol_item import *
from .stop_condition import *
from .visual import *

PROTOCOL_WIDGETS = {
    'bright_widget': visual.BrightWidget,
    'concentric_grating_widget': visual.ConcentricGratingWidget,
    'dark_widget': visual.DarkWidget,
    'dot_widget': visual.DotWidget,
    'following_dot_widget': visual.FollowingDotWidget,
    'looming_widget': visual.LoomingWidget,
    'following_looming_widget': visual.FollowingLoomingWidget,
    'okr_widget': visual.OKR_Widget,
    'omr_widget': visual.OMR_Widget,
    'phototaxis_widget': visual.PhototaxisWidget,
    'prey_capture_widget': visual.PreyCaptureWidget
}
