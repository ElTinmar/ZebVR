import json
from pathlib import Path
from typing import Union
from tracker import (
    AnimalTracker_CPU, AnimalTrackerParamTracking,
    BodyTracker_CPU, BodyTrackerParamTracking,
    EyesTracker_CPU, EyesTrackerParamTracking,
    TailTracker_CPU, TailTrackerParamTracking,
    SingleFishTracker_CPU, SingleFishTrackerParamTracking
)

def tracker_from_json(
        filename: Union[Path, str], 
        cam_fps: float,
        cam_pix_per_mm: float
    ) -> SingleFishTracker_CPU:
    
    filename = Path(filename)
    if filename.is_file():
        with open(filename) as fp:
            data = json.load(fp)
    else:
        print('file not found, using default tracker')
        data = {}
        data['animal_tracking'] = {
            'pix_per_mm': cam_pix_per_mm,
            'target_pix_per_mm': 5,
            'crop_dimension_mm': (7.5, 7.5)
        }

    animal_tracking_params = data.get('animal_tracking', {})
    body_tracking_params = data.get('body_tracking', None)
    eyes_tracking_params = data.get('eyes_tracking', None)
    tail_tracking_params = data.get('tail_tracking', None)

    animal = AnimalTracker_CPU(
        tracking_param=AnimalTrackerParamTracking(**animal_tracking_params),
    )
    body = eyes = tail = None
    
    if body_tracking_params is not None:
        body = BodyTracker_CPU(
            tracking_param=BodyTrackerParamTracking(**body_tracking_params), 
            fps = cam_fps
        )

    if eyes_tracking_params is not None:
        eyes = EyesTracker_CPU(
            tracking_param=EyesTrackerParamTracking(**eyes_tracking_params),
        )

    if tail_tracking_params is not None:
        tail = TailTracker_CPU(
            tracking_param=TailTrackerParamTracking(**tail_tracking_params),
        )

    tracker = SingleFishTracker_CPU(
        SingleFishTrackerParamTracking(
            animal = animal,
            body = body,
            eyes = eyes,
            tail = tail
        )
    )

    return tracker