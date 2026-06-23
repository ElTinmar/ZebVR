import json
from pathlib import Path
from typing import Union, Callable, Optional
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
    
    tail_tracking_params = settings.get('tail_tracking', None)
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
    eyes_tracking_params = settings.get('eyes_tracking', None)
    tail_tracking_params = settings.get('tail_tracking', None)

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

tracker_map: dict[str, Callable] = {
    'SingleFish': single_fish_tracker,
    'HeadEmbedded': head_embedded_tracker
}

def tracker_from_json(
        filename: Union[Path, str], 
        cam_fps: float,
        cam_pix_per_mm: float
    ) -> Tracker:
    
    filename = Path(filename)
    if filename.is_file():
        with open(filename) as fp:
            settings = json.load(fp)
    else:
        print('file not found, using default tracker')
        settings = {}

    tracker = tracker_map[settings.get('tracker', 'SingleFish')]
    id = settings.get('animal_identity', 0)
    controls = settings['substate'][str(id)]

    return tracker(controls, cam_fps, cam_pix_per_mm)