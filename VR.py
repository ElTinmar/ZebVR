from typing import Protocol
from numpy.typing import NDArray

class Camera(Protocol):
    def calibration() -> None: 
        ...

    def get_image() -> NDArray:
        ...

class Projector(Protocol):
    def calibration() -> None:
        ...

    def project(NDArray) -> None:
        ...

class Cam2Proj(Protocol):
    def registration():
        ...

    def transform(NDArray) -> NDArray:
        ...

class Tracker(Protocol):
    def track(NDArray) -> NDArray:
        ...

class Stimulus(Protocol):
    def update(NDArray) -> NDArray:
        ...


# 1. Connect hardware ----------------------------------------------------------

## 1.1 Camera . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 

## 1.2 Projector . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

# 2. Calibration ---------------------------------------------------------------

## 2.1 Camera . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 

## 2.2 Projector . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . 

# 3. Registration between camera and projector ---------------------------------

# 4. Estimate background -------------------------------------------------------

# 5. Tracking ------------------------------------------------------------------

# 6. Stimulation protocol ------------------------------------------------------

# 7. Multiprocessing pipeline --------------------------------------------------

# 8. Run experiment ------------------------------------------------------------

