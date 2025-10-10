import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, NamedTuple, Optional
import re
from re import Pattern
from video_tools import OpenCV_VideoReader
import pickle

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
        self.results: Path = self.root / 'results'
        self.plots: Path = self.root / 'plots'

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
    reader.open_file(str(video_file))
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
            stimuli = find_file(file_info, dir.stimuli, stimuli_filename_regexp, 'stim_', 'json'), # type: ignore
            tracking = find_file(file_info, dir.tracking, tracking_filename_regexp, 'tracking_', 'csv'), # type: ignore
            video = find_file(file_info, dir.video, video_filename_regexp, '', 'mp4'), # type: ignore
            video_timestamps = find_file(file_info, dir.video_timestamps, video_timestamps_filename_regexp, '', 'csv'), # type: ignore
            temperature = find_file(file_info, dir.temperature, temperature_filename_regexp, 'temperature_', 'csv', required=False)
        )
        experiments.append(exp)
    return experiments
