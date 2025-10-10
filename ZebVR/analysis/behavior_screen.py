import json
import pandas as pd
from pathlib import Path
from ZebVR.protocol import Stim
from typing import List, Dict, NamedTuple, Optional, Callable, Sequence, Tuple
import re
from re import Pattern
from video_tools import OpenCV_VideoReader
import pickle
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes

COLORS = ("#F1500A", "#0A6EF1")

class BehaviorData(NamedTuple):
    metadata: Dict
    stimuli: List[Dict]
    tracking: pd.DataFrame
    video: OpenCV_VideoReader #NOTE not sure yet about this
    video_timestamps: pd.DataFrame
    temperature: pd.DataFrame
    
class BehaviorFiles(NamedTuple):
    metadata: Path
    stimuli: Path
    tracking: Path
    video: Path
    video_timestamps: Path
    temperature: Optional[Path]

class Directories:
    def __init__(self, root: Path) -> None:
        self.root: Path = root
        self.metadata: Path = self.root / 'data' 
        self.stimuli: Path = self.root / 'data'
        self.tracking: Path = self.root / 'data'
        self.temperature: Path = self.root / 'data' 
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
temperature_filename_regexp = filename_regexp('temperature_','csv')
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

def load_metadata(metadata_file: Path) -> Dict:
    with open(metadata_file, 'rb') as f:
        metadata = pickle.load(f)
    return metadata

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

def load_temperature(temperature_file: Optional[Path]) -> pd.DataFrame:
    if temperature_file is None:
        return pd.DataFrame()
    return pd.read_csv(temperature_file)

def load_data(files: BehaviorFiles) -> BehaviorData:
    return BehaviorData(
        metadata = load_metadata(files.metadata),
        stimuli = load_stimuli(files.stimuli),
        tracking = load_tracking(files.tracking),
        video = load_video(files.video),
        video_timestamps = load_video_timestamps(files.video_timestamps),
        temperature = load_temperature(files.temperature)
    )

def find_file(file_info: FileNameInfo, dir: Path, regexp: Pattern, prefix: str, extension: str, required: bool = True) -> Optional[Path]:
    for file in dir.glob(f'{prefix}*.{extension}'):
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
        
    if required:
        raise FileNotFoundError(f"No matching video found for {file_info}")

def find_files(dir: Directories) -> List[BehaviorFiles]:
    metadata_files = list(dir.metadata.glob("*.metadata"))
    experiments = []
    for metadata_file in metadata_files:
        file_info = parse_filename(metadata_file, metadata_filename_regexp)
        exp = BehaviorFiles(
            metadata = metadata_file,
            stimuli = find_file(file_info, dir.stimuli, stimuli_filename_regexp, 'stim_', 'json'),
            tracking = find_file(file_info, dir.tracking, tracking_filename_regexp, 'tracking_', 'csv'),
            video = find_file(file_info, dir.video, video_filename_regexp, '', 'mp4'),
            video_timestamps = find_file(file_info, dir.video_timestamps, video_timestamps_filename_regexp, '', 'csv'),
            temperature = find_file(file_info, dir.temperature, temperature_filename_regexp, 'temperature_', 'csv', required=False)
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

# def superimpose_video_trials(behavior_data: BehaviorData) -> None:

#     stim_trials = get_trials(behavior_data)
#     for stim, stim_data in stim_trials.groupby('stim_select'):
#         for trial_idx, row in stim_data.iterrows():
#             video_segment = get_video_between(behavior_data, row['start_timestamp'], row['stop_timestamp'])

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
    
def common_time(trial_duration, fps) -> np.ndarray:
    num_points = int(fps * trial_duration)
    return np.linspace(0, trial_duration, num_points, endpoint=False)

def interpolate_ts(target_time, time, values) -> np.ndarray:
    return np.interp(target_time, time, values)

def plot_helper(
        ax: Axes,
        metrics: Dict,
        trial_duration_s: float,
        fps: float,
        group_names: List, 
        value_func: Callable, 
        group_func: Callable,
        color_func: Callable = lambda group_idx: 'k',
    ):

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
        ax.plot(
            target_time, 
            value,
            color = color_func(group_idx),
            alpha=0.2
        )
        trials[group_idx] = np.column_stack((trials[group_idx], value)) 

    for group_idx, name in enumerate(group_names):
        avg = np.mean(trials[group_idx], axis=1)
        sem = np.std(trials[group_idx], axis=1, ddof=1)
        ax.plot(target_time, avg, color = color_func(group_idx))
        ax.fill_between(
            target_time, 
            avg - sem, 
            avg + sem, 
            color = color_func(group_idx), 
            alpha = 0.2, 
            edgecolor = 'none'
        )

    ax.legend(group_names)

def plot_dark(metrics: Dict, ax: Sequence[Axes]):
    plot_helper(
        ax[0],
        metrics, 
        trial_duration_s = 30,
        fps = 100,
        group_names = ['dark'],
        value_func = lambda metrics, trial_idx: np.cumsum(metrics['distance_traveled'][trial_idx]),
        group_func = lambda metrics, trial_idx: 0,
        color_func = lambda group_idx: 'k'
    )
    ax[0].set_title('dark')
    plot_helper(
        ax[1],
        metrics, 
        trial_duration_s = 10,
        fps = 100,
        group_names = ['dark'],
        value_func = lambda metrics, trial_idx: metrics['heading_angle'][trial_idx],
        group_func = lambda metrics, trial_idx: 0, 
        color_func = lambda group_idx: 'k'
    )
    ax[1].set_title('loomings')

def plot_bright(metrics: Dict, ax: Axes):
    plot_helper(
        ax,
        metrics, 
        trial_duration_s = 30,
        fps = 100,
        group_names = ['bright'],
        value_func = lambda metrics, trial_idx: np.cumsum(metrics['distance_traveled'][trial_idx]),
        group_func = lambda metrics, trial_idx: 0,
        color_func = lambda group_idx: 'k'
    )
    ax.set_title('bright')

def plot_phototaxis(metrics: Dict, ax: Axes):
    plot_helper(
        ax,
        metrics, 
        trial_duration_s = 30,
        fps = 100,
        group_names = ['-1', '1'],
        value_func = lambda metrics, trial_idx: metrics['heading_angle'][trial_idx],
        group_func = lambda metrics, trial_idx: 0 if metrics['parameters'][trial_idx]['phototaxis_polarity'] == -1 else 1, # TODO check
        color_func = lambda group_idx: COLORS[group_idx]
    )
    ax.set_title('phototaxis')

def plot_omr(metrics: Dict, ax: Axes):
    plot_helper(
        ax,
        metrics, 
        trial_duration_s = 30,
        fps = 100,
        group_names = ['-90', '90'],
        value_func = lambda metrics, trial_idx: metrics['heading_angle'][trial_idx],
        group_func = lambda metrics, trial_idx: 0 if metrics['parameters'][trial_idx]['omr_angle_deg'] == -90 else 1, 
        color_func = lambda group_idx: COLORS[group_idx]
    )
    ax.set_title('omr')

def plot_okr(metrics: Dict, ax: Axes):
    plot_helper(
        ax,
        metrics, 
        trial_duration_s = 30,
        fps = 100,
        group_names = ['-36', '36'],
        value_func = lambda metrics, trial_idx: metrics['heading_angle'][trial_idx],
        group_func = lambda metrics, trial_idx: 0 if metrics['parameters'][trial_idx]['okr_speed_deg_per_sec'] == -36 else 1, 
        color_func = lambda group_idx: COLORS[group_idx]
    )
    ax.set_title('okr')

def plot_loomings(metrics: Dict, ax: Sequence[Axes]):
    plot_helper(
        ax[0],
        metrics, 
        trial_duration_s = 10,
        fps = 100,
        group_names = ['-2', '2'],
        value_func = lambda metrics, trial_idx: metrics['heading_angle'][trial_idx],
        group_func = lambda metrics, trial_idx: 0 if metrics['parameters'][trial_idx]['looming_center_mm'][0] == -2 else 1, 
        color_func = lambda group_idx: COLORS[group_idx]
    )
    ax[0].set_title('loomings')
    plot_helper(
        ax[1],
        metrics, 
        trial_duration_s = 10,
        fps = 100,
        group_names = [''],
        value_func = lambda metrics, trial_idx: metrics['speed'][trial_idx],
        group_func = lambda metrics, trial_idx: 0, 
        color_func = lambda group_idx: 'k'
    )
    ax[1].set_title('loomings')

def plot_prey_capture(metrics: Dict, ax: Axes):
    plot_helper(
        ax,
        metrics, 
        trial_duration_s = 30,
        fps = 100,
        group_names = ['-20', '20'],
        value_func = lambda metrics, trial_idx: metrics['heading_angle'][trial_idx],
        group_func = lambda metrics, trial_idx: 0 if metrics['parameters'][trial_idx]['prey_arc_start_deg'] == -20 else 1, 
        color_func = lambda group_idx: COLORS[group_idx]
    )
    ax.set_title('prey capture')

def plot_tracking_metrics(metrics: Dict):

    fig, axes = plt.subplots(3,3, figsize=(12,12))
    plot_dark(metrics[Stim.DARK], axes[0][0:2])
    plot_bright(metrics[Stim.BRIGHT], axes[0,2])
    plot_phototaxis(metrics[Stim.PHOTOTAXIS], axes[1,0])
    plot_omr(metrics[Stim.OMR], axes[1,1])
    plot_okr(metrics[Stim.OKR], axes[1,2])
    plot_prey_capture(metrics[Stim.PREY_CAPTURE], axes[2,0])
    plot_loomings(metrics[Stim.LOOMING], axes[2][1:3])
    plt.tight_layout()
    plt.show(block=False)
    
# TODO eye tracking OKR
# TODO eye tracking + tail tracking and classification J-turn PREY_CAPTURE
# TODO bout segmentation and distribution of heading change per bout
# TODO bout classification for every behavior + ethogram? 
# TODO overlay video trials
# TODO average trial-average over fish
# TODO plot trajectories / heatmap position for each stimulus 
 
if __name__ == '__main__':

    #base_dir = Path('/media/martin/MARTIN_8TB_0/Work/Baier/DATA/Behavioral_screen/output')
    base_dir = Path('/media/martin/DATA/Behavioral_screen/output')

    directories = Directories(base_dir)
    behavior_files: List[BehaviorFiles] = find_files(directories)
    for behavior_file in behavior_files:
        behavior_data: BehaviorData = load_data(behavior_file)
        metrics = compute_tracking_metrics(behavior_data)
        for identity, data in metrics.items():
            plot_tracking_metrics(data)
        