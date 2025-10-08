import json
import pandas as pd
from pathlib import Path
#from ZebVR.protocol import Stim
from typing import List, Dict, NamedTuple, Tuple
import re
from re import Pattern
from video_tools import OpenCV_VideoReader
import pickle
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

# TODO remove that
from enum import IntEnum
class Stim(IntEnum):
    DARK = 0
    BRIGHT = 1
    PHOTOTAXIS = 2
    OMR = 3
    OKR = 4
    LOOMING = 7
    PREY_CAPTURE = 6
    RAMP = 12

class BehaviorData(NamedTuple):
    metadata: str
    #metadata: Dict
    stimuli: List[Dict]
    tracking: pd.DataFrame
    video: OpenCV_VideoReader #NOTE not sure yet about this
    video_timestamps: pd.DataFrame
    
class BehaviorFiles(NamedTuple):
    metadata: Path
    stimuli: Path
    tracking: Path
    video: Path
    video_timestamps: Path

class Directories:
    def __init__(self, root: Path) -> None:
        self.root: Path = root
        self.metadata: Path = self.root / 'data' 
        self.stimuli: Path = self.root / 'data'
        self.tracking: Path = self.root / 'data'
        self.video: Path = self.root / 'video'
        self.video_timestamps: Path = self.root / 'video'

class FileNameInfo(NamedTuple):
    fish_id: int
    age: int
    line: str
    weekday: str
    day: int
    month: str
    year: int
    hour: int
    minute: int
    second: int

def filename_regexp(prefix: str, extension: str) -> Pattern:
    regexp = re.compile(
        f"^{prefix}"
        r"(?P<fish_id>\d{2})_"
        r"(?P<age>[0-9]+)dpf_"
        r"(?P<line>[^_]+)_"
        r"(?P<weekday>[A-Za-z]{3})_"
        r"(?P<day>\d{2})_"
        r"(?P<month>[A-Za-z]{3})_"
        r"(?P<year>\d{4})_"
        r"(?P<hour>\d{2})h"
        r"(?P<minute>\d{2})min"
        r"(?P<second>\d{2})sec\."
        f"{extension}$"
    )
    return regexp

metadata_filename_regexp = filename_regexp('','metadata')
stimuli_filename_regexp = filename_regexp('stim_','json')
tracking_filename_regexp = filename_regexp('tracking_','csv')
video_filename_regexp = filename_regexp('','mp4')
video_timestamps_filename_regexp = filename_regexp('','csv')

def parse_filename(path: Path, regexp: Pattern) -> FileNameInfo:
    m = regexp.match(path.name)
    if not m:
        raise ValueError(f"Filename does not match expected pattern: {path.name}")
    g = m.groupdict()
    return FileNameInfo(
        fish_id = int(g["fish_id"]),
        age = int(g["age"]),
        line = g["line"],
        weekday = g["weekday"],
        day = int(g["day"]),
        month = g["month"],
        year = int(g["year"]),
        hour = int(g["hour"]),
        minute = int(g["minute"]),
        second = int(g["second"])
    )

def load_metadata(metadata_file: Path) -> str:
    with open(metadata_file, 'r') as f:
        metadata = f.read()
    return metadata

# def load_metadata(metadata_file: Path) -> Dict:
#     with open(metadata_file, 'rb') as f:
#         metadata = pickle.load(f)
#     return metadata

def load_stimuli(stim_file: Path) -> List[Dict]:
    stimuli = []
    with open(stim_file) as f:
        for line in f:
            stimuli.append(json.loads(line))
    return stimuli

def load_tracking(tracking_file: Path) -> pd.DataFrame:
    return pd.read_csv(tracking_file)

def load_video(video_file: Path) -> OpenCV_VideoReader:
    reader = OpenCV_VideoReader()
    reader.open_file(video_file.as_posix())
    return reader 

def load_video_timestamps(video_timestamp_file: Path) -> pd.DataFrame:
    return pd.read_csv(video_timestamp_file)

def load_data(files: BehaviorFiles) -> BehaviorData:
    return BehaviorData(
        metadata = load_metadata(files.metadata),
        stimuli = load_stimuli(files.stimuli),
        tracking = load_tracking(files.tracking),
        video = load_video(files.video),
        video_timestamps = load_video_timestamps(files.video_timestamps)
    )

def find_file(file_info: FileNameInfo, dir: Path, regexp: Pattern, extension: str) -> Path:
    for file in dir.glob(extension):
        info = parse_filename(file, regexp)
        if (
            info.fish_id == file_info.fish_id and
            info.age == file_info.age and
            info.line == file_info.line and
            info.day == file_info.day and
            info.month == file_info.month and
            info.year == file_info.year
        ):
            return file
    raise FileNotFoundError(f"No matching video found for {file_info}")

def find_files(dir: Directories) -> List[BehaviorFiles]:
    metadata_files = list(dir.metadata.glob("*.metadata"))
    experiments = []
    for metadata_file in metadata_files:
        file_info = parse_filename(metadata_file, metadata_filename_regexp)
        exp = BehaviorFiles(
            metadata = metadata_file,
            stimuli = find_file(file_info, dir.stimuli, stimuli_filename_regexp, '*.json'),
            tracking = find_file(file_info, dir.tracking, tracking_filename_regexp, '*.csv'),
            video = find_file(file_info, dir.video, video_filename_regexp, '*.mp4'),
            video_timestamps = find_file(file_info, dir.video_timestamps, video_timestamps_filename_regexp, '*.csv')
        )
        experiments.append(exp)
    return experiments

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

def compute_tracking_metrics(behavior_data: BehaviorData) -> Dict:
    
    stim_trials = get_trials(behavior_data)

    # change that 
    match = re.search(r"'pix_per_mm':\s*([\d.]+)", behavior_data.metadata)
    if match is None:
        raise RuntimeError('pix per mm not found')
    mm_per_pix = 1/float(match.group(1))

    #behavior_data.metadata['calibration']['pix_per_mm']

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

def plot_dark(metrics: Dict, ax: Axes):
    num_trials = len(metrics['relative_time'])
    for trial_idx in range(num_trials):
        ax.plot(
            metrics['relative_time'][trial_idx], 
            np.cumsum(metrics['distance_traveled'][trial_idx])
        )
    ax.set_title('dark')

def plot_bright(metrics: Dict, ax: Axes):
    num_trials = len(metrics['relative_time'])
    for trial_idx in range(num_trials):
        ax.plot(
            metrics['relative_time'][trial_idx], 
            np.cumsum(metrics['distance_traveled'][trial_idx])
        )
    ax.set_title('bright')

def plot_phototaxis(metrics: Dict, ax: Axes):
    num_trials = len(metrics['relative_time'])
    for trial_idx in range(num_trials):
        ax.plot(
            metrics['relative_time'][trial_idx], 
            metrics['heading_angle'][trial_idx],
            color = "#F1500A" if metrics['parameters'][trial_idx]['phototaxis_polarity'] == -1 else "#0A6EF1"
        )
    ax.set_title('phototaxis')

def plot_omr(metrics: Dict, ax: Axes):
    num_trials = len(metrics['relative_time'])
    for trial_idx in range(num_trials):
        ax.plot(
            metrics['relative_time'][trial_idx], 
            metrics['heading_angle'][trial_idx],
            color = "#F1500A" if metrics['parameters'][trial_idx]['omr_angle_deg'] == -90 else "#0A6EF1"
        )
    ax.set_title('omr')

def plot_okr(metrics: Dict, ax: Axes):
    num_trials = len(metrics['relative_time'])
    for trial_idx in range(num_trials):
        ax.plot(
            metrics['relative_time'][trial_idx], 
            metrics['heading_angle'][trial_idx],
            color = "#F1500A" if metrics['parameters'][trial_idx]['okr_speed_deg_per_sec'] == -36 else "#0A6EF1"
        )
    ax.set_title('okr')

def plot_loomings(metrics: Dict, ax: Axes):
    num_trials = len(metrics['relative_time'])
    for trial_idx in range(num_trials):
        ax.plot(
            metrics['relative_time'][trial_idx], 
            metrics['speed'][trial_idx]
        )
    ax.set_title('loomings')

def plot_prey_capture(metrics: Dict, ax: Axes):
    ...

def plot_tracking_metrics(metrics: Dict):

    fig, axes = plt.subplots(3,3, figsize=(12,12))
    plot_dark(metrics[Stim.DARK], axes[0,0])
    plot_bright(metrics[Stim.BRIGHT], axes[0,1])
    plot_phototaxis(metrics[Stim.PHOTOTAXIS], axes[0,2])
    plot_omr(metrics[Stim.OMR], axes[1,0])
    plot_okr(metrics[Stim.OKR], axes[1,1])
    plot_loomings(metrics[Stim.LOOMING], axes[1,2])
    plot_prey_capture(metrics[Stim.PREY_CAPTURE], axes[2,0])
    plt.tight_layout()
    plt.show(block=False)
    
if __name__ == '__main__':

    base_dir = Path('/media/martin/MARTIN_8TB_0/Work/Baier/DATA/Behavioral_screen/output')
    directories = Directories(base_dir)
    behavior_files: List[BehaviorFiles] = find_files(directories)
    for behavior_file in behavior_files:
        behavior_data: BehaviorData = load_data(behavior_file)
        metrics = compute_tracking_metrics(behavior_data)
        for identity, data in metrics.items():
            plot_tracking_metrics(data)
        