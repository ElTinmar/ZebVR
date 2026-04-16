import pandas as pd
from typing import (
    Dict, 
    Callable, 
    Tuple, 
    List, 
    Iterable, 
    TypedDict, 
)
import numpy as np
from tqdm import tqdm
from video_tools import OpenCV_VideoWriter, OpenCV_VideoReader
from ZebVR.protocol import Stim
import cv2
from .load import BehaviorData, BehaviorFiles, Directories
from qt_widgets import imshow, waitKey

class WellDimensions(TypedDict):
    well_radius_mm: float
    distance_between_well_centers_mm: float
    
# TODO put right dimensions here
AGAROSE_WELL_DIMENSIONS: WellDimensions = {
    'well_radius_mm': 19.5/2,
    'distance_between_well_centers_mm': 22
}

def get_background_image(
        behavior_data: BehaviorData, 
        num_samples: int = 100
    ) -> np.ndarray:

    height = behavior_data.video.get_height()
    width = behavior_data.video.get_width()
    num_frames = behavior_data.video.get_number_of_frame()
    samples = np.linspace(0, num_frames, num_samples, endpoint=False, dtype=int)
    video_samples = np.zeros((height, width, num_samples), dtype=np.uint8)

    for i, frame_idx in enumerate(samples):
        behavior_data.video.seek_to(frame_idx)
        _, frame = behavior_data.video.next_frame()
        video_samples[:,:,i] = frame[:,:,0]

    background_image = np.median(video_samples, axis=2).astype(np.uint8)
    return background_image

def get_circles(
        image: np.ndarray, 
        pix_per_mm: float,
        tolerance_mm: float,
        well_dimensions: WellDimensions
    ) -> np.ndarray:

    tolerance = int(tolerance_mm * pix_per_mm) 

    circle_radius = int(pix_per_mm * well_dimensions['well_radius_mm'])
    min_radius = circle_radius - tolerance
    max_radius = circle_radius + tolerance

    well_distance = pix_per_mm * well_dimensions['distance_between_well_centers_mm']
    min_distance = well_distance - tolerance

    circles = cv2.HoughCircles(
        image,
        cv2.HOUGH_GRADIENT,
        dp = 1,
        minDist = min_distance,
        param1 = 50,
        param2 = 30,
        minRadius = min_radius,
        maxRadius = max_radius
    )[0]

    return circles

def show_detected_circles(image: np.ndarray, circles: np.ndarray) -> None:

    if len(image.shape) == 2:  # grayscale
        img_color = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    else:
        img_color = image.copy()

    circles = np.around(circles).astype(np.uint16)
    for x, y, radius in circles:
        center = (x, y)
        cv2.circle(img_color, center, radius, (0, 255, 0), 2)
        cv2.circle(img_color, center, 2, (0, 0, 255), 3)

    imshow('detected wells', img_color)
    waitKey(0)

def circle_roi_index(circles: np.ndarray, rois: List[Tuple[int,int,int,int]]):
    indices = []
    for x, y, _ in circles:
        index = -1
        for i, (rx, ry, rw, rh) in enumerate(rois):
            if rx <= x < rx + rw and ry <= y < ry + rh:
                index = i
        
        if index == -1:
            RuntimeError('Circle does not belong to any ROI')
        
        indices.append(index)
    return indices

def get_well_coords_mm(
        behavior_data: BehaviorData, 
        num_samples: int = 100,
        tolerance_mm = 2,
    ) -> np.ndarray:

    background_image = get_background_image(behavior_data, num_samples)
    pix_per_mm = behavior_data.metadata['calibration']['pix_per_mm']
    circles = get_circles(
        background_image, 
        pix_per_mm, 
        tolerance_mm, 
        AGAROSE_WELL_DIMENSIONS
    )
    show_detected_circles(background_image, circles)
    ind = circle_roi_index(circles, behavior_data.metadata['identity']['ROIs'])
    circles_mm = 1/pix_per_mm * circles[ind,:]

    return circles_mm
    
def get_trials(
        behavior_data: BehaviorData, 
        keep_stim: Iterable[Stim] = [stim for stim in Stim]
    ) -> pd.DataFrame:

    last_timestamp = max(
        behavior_data.tracking['timestamp'].max(),
        behavior_data.video_timestamps['timestamp'].max()
    )

    rows = []
    for i, stim_dict in enumerate(behavior_data.stimuli):
        start_timestamp = stim_dict["timestamp"]
        stop_timestamp = behavior_data.stimuli[i + 1]["timestamp"] if i + 1 < len(behavior_data.stimuli) else last_timestamp
        stim_select = int(stim_dict["stim_select"])

        row = {
            "stim_select": stim_select,
            "start_timestamp": start_timestamp,
            "stop_timestamp": stop_timestamp,
            "start_time_sec": stim_dict.get("start_time_sec", pd.NA),
            "prey_arc_start_deg": stim_dict.get("prey_arc_start_deg", pd.NA),
            "phototaxis_polarity": stim_dict.get("phototaxis_polarity", pd.NA),
            "omr_angle_deg": stim_dict.get("omr_angle_deg", pd.NA),
            "okr_speed_deg_per_sec": stim_dict.get("okr_speed_deg_per_sec", pd.NA),
            "looming_center_mm_x": stim_dict.get("looming_center_mm", [pd.NA, pd.NA])[0],
            "foreground_color": str(stim_dict["foreground_color"]),
            "background_color": str(stim_dict["background_color"]),
        }

        if Stim(stim_select) in keep_stim:
            rows.append(row)

    return pd.DataFrame(rows)

def get_tracking_between(
        tracking_data: pd.DataFrame, 
        start_timestamp: int, 
        stop_timestamp: int
    ) -> pd.DataFrame:
    
    df = tracking_data.sort_values('timestamp').reset_index(drop=True)
    mask = (df['timestamp'] >= start_timestamp) & (df['timestamp'] <= stop_timestamp)
    segment = df.loc[mask].copy()
    return segment

def get_relative_time_sec(tracking_data: pd.DataFrame) -> pd.Series:
    relative_time = tracking_data['timestamp'] - tracking_data['timestamp'].iloc[0]
    return relative_time*1e-9

def get_theta(tracking_data: pd.DataFrame) -> Tuple[np.ndarray, pd.Series]:
    angle = np.arctan2(tracking_data['pc1_y'], tracking_data['pc1_x'])
    notna = ~np.isnan(angle)
    angle_unwrapped = pd.Series(np.nan, index=tracking_data.index, dtype=float)
    angle_unwrapped[notna] = np.unwrap(angle[notna]) 
    return angle, angle_unwrapped - angle_unwrapped.iloc[0] 

def get_distance_mm(tracking_data: pd.DataFrame, mm_per_pix: float) -> pd.Series:
    x = tracking_data['centroid_x'].astype(float)
    y = tracking_data['centroid_y'].astype(float)
    x_diff = x.diff()
    y_diff = y.diff()
    distance = mm_per_pix * (x_diff**2 + y_diff**2)**0.5
    return distance

def get_speed_mm_per_sec(tracking_data: pd.DataFrame, mm_per_pix: float) -> pd.Series:
    dx = get_distance_mm(tracking_data, mm_per_pix)
    dt = get_relative_time_sec(tracking_data).diff()
    return dx/dt

def get_coordinates_mm(
        tracking_data: pd.DataFrame, 
        mm_per_pix: float, 
        arena_center_mm: np.ndarray
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:

    x_mm = (tracking_data['centroid_x'] * mm_per_pix) - arena_center_mm[0]
    y_mm = (tracking_data['centroid_y'] * mm_per_pix) - arena_center_mm[1]
    radial_distance_mm = (x_mm**2 + y_mm**2)**0.5
    return x_mm, y_mm, radial_distance_mm

def common_time(trial_duration, fps) -> np.ndarray:
    num_points = int(fps * trial_duration)
    return np.linspace(0, trial_duration, num_points, endpoint=False)

def interpolate_ts(target_time, time, values) -> np.ndarray:
    return np.interp(target_time, time, values)

class TrialMetrics(TypedDict):
    relative_time: List[pd.Series]
    theta_unwrapped: List[pd.Series]
    distance_traveled: List[pd.Series]
    speed: List[pd.Series]
    parameters: List[pd.Series]
    x: List[pd.Series]
    y: List[pd.Series]
    theta: List[np.ndarray]
    distance_from_center: List[pd.Series]

def extract_metrics(
        behavior_data: BehaviorData, 
        well_coords_mm: np.ndarray
    ) -> Dict[int, Dict[Stim, TrialMetrics]]:
    
    stim_trials = get_trials(behavior_data)
    mm_per_pix = 1/float(behavior_data.metadata['calibration']['pix_per_mm'])

    metrics = {}
    for identity, data in behavior_data.tracking.groupby('identity'):
        metrics[identity] = {}
        for stim_select, stim_data in stim_trials.groupby('stim_select'):
            stim = Stim(stim_select)
            metrics[identity][stim] = {}
            metrics[identity][stim]['relative_time'] = []
            metrics[identity][stim]['theta_unwrapped'] = []
            metrics[identity][stim]['distance_traveled'] = [] 
            metrics[identity][stim]['speed'] = [] 
            metrics[identity][stim]['parameters'] = []
            metrics[identity][stim]['x'] = []
            metrics[identity][stim]['y'] = []
            metrics[identity][stim]['theta'] = []
            metrics[identity][stim]['distance_from_center'] = []
            for trial_idx, row in stim_data.iterrows():
                segment = get_tracking_between(data, row['start_timestamp'], row['stop_timestamp'])
                metrics[identity][stim]['relative_time'].append(get_relative_time_sec(segment))
                metrics[identity][stim]['distance_traveled'].append(get_distance_mm(segment, mm_per_pix))
                metrics[identity][stim]['speed'].append(get_speed_mm_per_sec(segment, mm_per_pix))
                x_mm, y_mm, radial_distance_mm = get_coordinates_mm(segment, mm_per_pix, well_coords_mm[identity,:])
                theta, theta_unwrapped = get_theta(segment)
                metrics[identity][stim]['theta_unwrapped'].append(theta_unwrapped)
                metrics[identity][stim]['x'].append(x_mm)
                metrics[identity][stim]['y'].append(y_mm)
                metrics[identity][stim]['theta'].append(theta)
                metrics[identity][stim]['distance_from_center'].append(radial_distance_mm)
                metrics[identity][stim]['parameters'].append(row)
                
    return metrics

# TODO
def analyse_helper(
        metrics: Dict,
        trial_duration_s: float,
        fps: float,
        group_names: List, 
        value_func: Callable, 
        group_func: Callable,
    ) -> Tuple[List[np.ndarray], List[np.ndarray], List[np.ndarray]]:

    num_trials = len(metrics['relative_time'])
    target_time = common_time(trial_duration_s, fps)
    trials = [np.zeros((len(target_time), 0)), np.zeros((len(target_time), 0))] 

    for trial_idx in range(num_trials):
        group_idx = group_func(metrics, trial_idx)
        value = interpolate_ts(
            target_time, 
            metrics['relative_time'][trial_idx],
            value_func(metrics, trial_idx)
        )
        trials[group_idx] = np.column_stack((trials[group_idx], value)) 

    avg = []
    sem = []
    for group_idx, name in enumerate(group_names):
        avg.append(np.mean(trials[group_idx], axis=1))
        sem.append(np.std(trials[group_idx], axis=1, ddof=1))

    return trials, avg, sem

def timestamp_to_frame_index(behavior_data: BehaviorData, timestamp: int) -> int:
    distance = behavior_data.video_timestamps['timestamp'] - timestamp
    idx_closest = distance.abs().argmin()
    frame_index = behavior_data.video_timestamps['index'][idx_closest]
    return frame_index

GROUPING_PARAMETER = {
    Stim.DARK: 'background_color',
    Stim.BRIGHT: 'foreground_color',
    Stim.PHOTOTAXIS: 'phototaxis_polarity',
    Stim.OMR: 'omr_angle_deg',
    Stim.OKR: 'okr_speed_deg_per_sec',
    Stim.LOOMING: 'looming_center_mm_x',
    Stim.PREY_CAPTURE: 'prey_arc_start_deg'
}

def superimpose_video_trials(
        directories: Directories,
        behavior_data: BehaviorData,
        behavior_file: BehaviorFiles,
        trial_duration_sec: float,
        grouping_parameter: Dict[Stim, str] = GROUPING_PARAMETER
    ) -> None:

    directories.results.mkdir(parents=True, exist_ok=True)
    
    height = behavior_data.metadata['camera']['height_value']
    width = behavior_data.metadata['camera']['width_value']
    fps = int(behavior_data.metadata['camera']['framerate_value'])
    num_frames = int(trial_duration_sec * behavior_data.metadata['camera']['framerate_value'])

    stim_trials = get_trials(
        behavior_data,
        grouping_parameter.keys()
    )
    for stim, stim_data in tqdm(stim_trials.groupby('stim_select')):
        for parameter_value, data in stim_data.groupby(grouping_parameter[Stim(stim)]):
            
            output_path = directories.results / f"{behavior_file.video.stem}_{Stim(stim)}_{grouping_parameter[Stim(stim)]}_{parameter_value}.mp4"
            writer = OpenCV_VideoWriter(
                height = height, 
                width = width,
                fps = fps,
                filename = str(output_path),
                fourcc = 'mp4v'
            )

            readers = []
            for start_timestamp in data['start_timestamp']:
                frame_index_start = timestamp_to_frame_index(behavior_data, start_timestamp)
                reader = OpenCV_VideoReader()
                reader.open_file(str(behavior_file.video))
                reader.seek_to(frame_index_start)
                readers.append(reader)

            num_trials = len(data['start_timestamp'])
            mip = np.zeros((height, width, num_trials), dtype=np.uint8)
            for _ in tqdm(range(num_frames)):
                for trial_idx in range(num_trials):
                    _, frame = readers[trial_idx].next_frame()
                    mip[:,:,trial_idx] =  frame[:,:,0]
                writer.write_frame(np.min(mip, axis=2))

            writer.close()

