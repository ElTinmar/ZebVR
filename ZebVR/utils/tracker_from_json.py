import json
from pathlib import Path
from typing import Union, Optional
from tracker import (
    Tracker,
    AnimalTracker_CPU, AnimalTrackerParamTracking,
    BodyTracker_CPU, BodyTrackerParamTracking,
    EyesTracker_CPU, EyesTrackerParamTracking,
    TailTracker_CPU, TailTrackerParamTracking,
    SingleFishTracker_CPU, SingleFishTrackerParamTracking,
    HeadEmbeddedTracker_CPU, HeadEmbedded_ParamTracking, LighthillPredictor
)

def head_embedded_tracker(settings: dict, cam_fps: float, cam_pix_per_mm: Optional[float] = None) -> HeadEmbeddedTracker_CPU:
    
    tail_tracking_params = settings.get('tail_tracking', {})
    tail = TailTracker_CPU(
        tracking_param=TailTrackerParamTracking(**tail_tracking_params),
    )

    predictor = LighthillPredictor(
        forward_gain = settings.get('forward_gain', 0.08),
        angular_gain = settings.get('angular_gain', 0.01),
        time_window_ms = settings.get('time_window_ms', 30),
        framerate = cam_fps,
        tau = settings.get('tau', 0.0),
    )

    tracker = HeadEmbeddedTracker_CPU(
        HeadEmbedded_ParamTracking(
            tail = tail,
            position_predictor = predictor,
            centroid_x = settings.get('centroid_x', 0),
            centroid_y = settings.get('centroid_y', 0),
            heading_angle_rad =  settings.get('heading_angle_rad', 0)
        )
    )

    return tracker

def single_fish_tracker(settings: dict, cam_fps: float, cam_pix_per_mm: Optional[float] = None) -> SingleFishTracker_CPU:

    if cam_pix_per_mm is None:
        cam_pix_per_mm = settings.get('pix_per_mm', 10)

    animal_tracking_params = settings.get('animal_tracking', 
        {'pix_per_mm': cam_pix_per_mm,
        'target_pix_per_mm': 5,
        'crop_dimension_mm': (7.5, 7.5)}
    )
    body_tracking_params = settings.get('body_tracking', None)
    body_tracking_enabled = settings.get('body_tracking_enabled', False)
    eyes_tracking_params = settings.get('eyes_tracking', None)
    eyes_tracking_enabled = settings.get('eyes_tracking_enabled', False)
    tail_tracking_params = settings.get('tail_tracking', None)
    tail_tracking_enabled = settings.get('tail_tracking_enabled', False)

    animal = AnimalTracker_CPU(
        tracking_param=AnimalTrackerParamTracking(**animal_tracking_params),
    )
    body = eyes = tail = None
    
    if body_tracking_enabled and body_tracking_params is not None:
        body = BodyTracker_CPU(
            tracking_param=BodyTrackerParamTracking(**body_tracking_params), 
            fps = cam_fps
        )

    if eyes_tracking_enabled and eyes_tracking_params is not None:
        eyes = EyesTracker_CPU(
            tracking_param=EyesTrackerParamTracking(**eyes_tracking_params),
        )

    if tail_tracking_enabled and tail_tracking_params is not None:
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

def tracker_from_json(
        filename: Union[Path, str], 
        cam_fps: float,
        cam_pix_per_mm: float,
        head_embedded: bool = False
    ) -> Tracker:
    
    filename = Path(filename)
    if filename.is_file():
        with open(filename) as fp:
            settings = json.load(fp)
    else:
        tracker_type = 'head embedded' if head_embedded else 'single fish'
        print(f'{filename} not found, using default {tracker_type} tracker settings')
        settings = {}

    id = settings.get('animal_identity', 0)
    substate = settings.get('substate', {})
    controls = substate.get(str(id), {})

    if head_embedded:
        return head_embedded_tracker(controls, cam_fps, cam_pix_per_mm)
    
    return single_fish_tracker(controls, cam_fps, cam_pix_per_mm)