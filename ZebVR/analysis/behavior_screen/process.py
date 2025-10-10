import pandas as pd
from typing import  Dict, Callable, Tuple, List
import numpy as np
from tqdm import tqdm
from video_tools import OpenCV_VideoWriter, OpenCV_VideoReader
from ZebVR.protocol import Stim
from .load import BehaviorData, BehaviorFiles, Directories

def get_trials(behavior_data: BehaviorData) -> pd.DataFrame:

    last_timestamp = max(
        behavior_data.tracking['timestamp'].max(),
        behavior_data.video_timestamps['timestamp'].max()
    )

    rows = []
    for i, stim_dict in enumerate(behavior_data.stimuli):
        start_timestamp = stim_dict["timestamp"]
        stop_timestamp = behavior_data.stimuli[i + 1]["timestamp"] if i + 1 < len(behavior_data.stimuli) else last_timestamp

        row = {
            "stim_select": int(stim_dict["stim_select"]),
            "start_timestamp": start_timestamp,
            "stop_timestamp": stop_timestamp,
            "start_time_sec": stim_dict.get("start_time_sec", pd.NA),
        }

        for key, val in stim_dict.items():
            if key not in ["stim_select", "timestamp", "start_time_sec"]:
                row[key] = val

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

def get_heading_angle_deg(tracking_data: pd.DataFrame) -> pd.Series:
    angle = np.arctan2(tracking_data['pc1_y'], tracking_data['pc1_x'])
    notna = ~np.isnan(angle)
    angle_unwrapped = pd.Series(np.nan, index=tracking_data.index, dtype=float)
    angle_unwrapped[notna] = np.unwrap(angle[notna]) 
    angle_unwrapped_deg = angle_unwrapped * 180/np.pi
    return angle_unwrapped_deg - angle_unwrapped_deg.iloc[0] 

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
    
def common_time(trial_duration, fps) -> np.ndarray:
    num_points = int(fps * trial_duration)
    return np.linspace(0, trial_duration, num_points, endpoint=False)

def interpolate_ts(target_time, time, values) -> np.ndarray:
    return np.interp(target_time, time, values)

def compute_tracking_metrics(behavior_data: BehaviorData) -> Dict:
    
    stim_trials = get_trials(behavior_data)
    mm_per_pix = 1/float(behavior_data.metadata['calibration']['pix_per_mm'])

    metrics = {}
    for identity, data in behavior_data.tracking.groupby('identity'):
        metrics[identity] = {}
        for stim, stim_data in stim_trials.groupby('stim_select'):
            metrics[identity][stim] = {}
            metrics[identity][stim]['relative_time'] = []
            metrics[identity][stim]['heading_angle'] = []
            metrics[identity][stim]['distance_traveled'] = [] 
            metrics[identity][stim]['speed'] = [] 
            metrics[identity][stim]['parameters'] = []

            for trial_idx, row in stim_data.iterrows():
                segment = get_tracking_between(data, row['start_timestamp'], row['stop_timestamp'])
                metrics[identity][stim]['relative_time'].append(get_relative_time_sec(segment))
                metrics[identity][stim]['heading_angle'].append(get_heading_angle_deg(segment))
                metrics[identity][stim]['distance_traveled'].append(get_distance_mm(segment, mm_per_pix=mm_per_pix))
                metrics[identity][stim]['speed'].append(get_speed_mm_per_sec(segment, mm_per_pix=mm_per_pix))
                metrics[identity][stim]['parameters'].append(row)
                
    return metrics

def compute_trajectories(behavior_data: BehaviorData) -> Dict:

    stim_trials = get_trials(behavior_data)
    mm_per_pix = 1/float(behavior_data.metadata['calibration']['pix_per_mm'])

    trajectories = {}
    for identity, data in behavior_data.tracking.groupby('identity'):
        trajectories[identity] = {}
        for stim, stim_data in stim_trials.groupby('stim_select'):
            trajectories[identity][stim] = {}
            trajectories[identity][stim]['x'] = []
            trajectories[identity][stim]['y'] = []
            trajectories[identity][stim]['parameters'] = []
            for trial_idx, row in stim_data.iterrows():
                segment = get_tracking_between(data, row['start_timestamp'], row['stop_timestamp'])
                trajectories[identity][stim]['x'].append(segment['centroid_x'] * mm_per_pix)
                trajectories[identity][stim]['y'].append(segment['centroid_y'] * mm_per_pix)
                trajectories[identity][stim]['parameters'].append(row)
    
    return trajectories

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

def superimpose_video_trials(
        directories: Directories,
        behavior_data: BehaviorData,
        behavior_file: BehaviorFiles,
        trial_duration_sec: float
    ) -> None:

    directories.results.mkdir(parents=True, exist_ok=True)
    
    height = behavior_data.metadata['camera']['height_value']
    width = behavior_data.metadata['camera']['width_value']
    fps = int(behavior_data.metadata['camera']['framerate_value'])
    num_frames = int(trial_duration_sec * behavior_data.metadata['camera']['framerate_value'])

    stim_trials = get_trials(behavior_data)
    for stim, stim_data in tqdm(stim_trials.groupby('stim_select')):
        num_trials = len(stim_data['start_timestamp'])
        output_path = directories.results / f"{behavior_file.video.stem}_{Stim(stim)}.mp4"

        writer = OpenCV_VideoWriter(
            height = height, 
            width = width,
            fps = fps,
            filename = str(output_path),
            fourcc = 'mp4v'
        )

        readers = []
        for start_timestamp in stim_data['start_timestamp']:
            frame_index_start = timestamp_to_frame_index(behavior_data, start_timestamp)
            reader = OpenCV_VideoReader()
            reader.open_file(str(behavior_file.video))
            reader.seek_to(frame_index_start)
            readers.append(reader)

        mip = np.zeros((height, width, num_trials), dtype=np.uint8)
        for _ in tqdm(range(num_frames)):
            for trial_idx in range(num_trials):
                _, frame = readers[trial_idx].next_frame()
                mip[:,:,trial_idx] =  frame[:,:,0]
            writer.write_frame(np.min(mip, axis=2))

        writer.close()

