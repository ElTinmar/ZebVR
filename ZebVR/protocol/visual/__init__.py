from .bright import Bright, BrightWidget
from .ramp import Ramp, RampWidget
from .concentric_grating import ConcentricGrating, ConcentricGratingWidget
from .dark import Dark, DarkWidget
from .dot import Dot, FollowingDot, DotWidget, FollowingDotWidget
from .image import Image, ImageWidget
from .looming import (
    LinearRadiusLooming, 
    LinearRadiusLoomingCL, 
    LinearRadiusLoomingWidget, 
    LinearRadiusLoomingCL_Widget,
    LinearAngleLooming, 
    LinearAngleLoomingCL, 
    LinearAngleLoomingWidget, 
    LinearAngleLoomingCL_Widget,
    ConstantApproachSpeedLooming,
    ConstantApproachSpeedLoomingCL,
    ConstantApproachSpeedLoomingWidget,
    ConstantApproachSpeedLoomingCL_Widget,
)
from .okr import OKR_CLOSED_LOOP, OKR_Widget
from .omr import OMR_CLOSED_LOOP, OMR_Widget
from .phototaxis import Phototaxis, PhototaxisWidget
from .prey_capture import (
    PreyCapture, 
    PreyCaptureWidget, 
    FollowingPreyCapture, 
    FollowingPreyCaptureWidget
)
