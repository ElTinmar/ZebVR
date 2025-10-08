import json
import pandas as pd
from pathlib import Path
from ZebVR.protocol import Stim
from typing import List, Dict, NamedTuple, Optional
import re
from re import Pattern
from video_tools import OpenCV_VideoReader

class BehaviorData(NamedTuple):
    metadata: str #TODO maybe smarter metadata export in GUI so that we can load this as pure dict
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
        r"(?P<line>[A-Za-z0-9]+)_"
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

def load_metadata(metadata_file: Path) -> str:
    with open(metadata_file, 'r') as f:
        metadata = f.read()
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

def load_data(files: BehaviorFiles) -> BehaviorData:
    return BehaviorData(
        metadata = load_metadata(files.metadata),
        stimuli = load_stimuli(files.stimuli),
        tracking = load_tracking(files.tracking),
        video = load_video(files.video),
        video_timestamps = load_video_timestamps(files.video_timestamps)
    )
    
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

def get_trials(behavior_data: BehaviorData):

    trials = {}

    for i, stim in enumerate(behavior_data.stimuli):

        start_time = stim["timestamp"]
        if i < len(behavior_data.stimuli) - 1:
            end_time = behavior_data.stimuli[i+1]["timestamp"]
        else:
            end_time = None  # TODO 
        
        stim_num = int(stim['stim_select'])
        stim = Stim(stim_num)

        if stim not in 


if __name__ == '__main__':

    base_dir = Path('/media/martin/MARTIN_8TB_0/Work/Baier/DATA/Behavioral_screen/output')
    directories = Directories(base_dir)
    behavior_files: List[BehaviorFiles] = find_files(directories)

    for behavior_file in behavior_files:
        behavior_data: BehaviorData = load_data(behavior_file)
        break
