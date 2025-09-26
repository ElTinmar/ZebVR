import json
import pandas as pd
import subprocess
from enum import IntEnum
from pathlib import Path

class Stim(IntEnum):

    # visual
    DARK = 0
    BRIGHT = 1
    PHOTOTAXIS = 2
    OMR = 3
    OKR = 4
    FOLLOWING_LOOMING = 5
    PREY_CAPTURE = 6
    LOOMING = 7
    CONCENTRIC_GRATING = 8
    FOLLOWING_DOT = 9
    DOT = 10
    IMAGE = 11
    RAMP = 12

    def __str__(self):
        return self.name

base_folder = Path('/media/martin/DATA/Behavioral_screen/extract_video')
timestamp_file = base_folder / '00_07dpf_TLN-7432_Thu_25_Sep_2025_17h28min28sec.csv'
stim_file = base_folder / 'stim_00_07dpf_TLN-7432_Thu_25_Sep_2025_17h28min44sec.json'
video_file = base_folder / '00_07dpf_TLN-7432_Thu_25_Sep_2025_17h28min28sec.mp4'
        
# Load timestamp mapping
ts_df = pd.read_csv(timestamp_file, sep=",")

# Load stim events
events = []
with open(stim_file) as f:
    for line in f:
        events.append(json.loads(line))

# Convert stim timestamps -> video times
def timestamp_to_video(ts):
    idx = ts_df["timestamp"].sub(ts).abs().idxmin()
    return ts_df.loc[idx, "camera_timestamp"]

stim_counter = {}
for member in Stim:
    stim_counter[member] = 0

for i, ev in enumerate(events):
    start_time = timestamp_to_video(ev["timestamp"])
    if i < len(events) - 1:
        end_time = timestamp_to_video(events[i+1]["timestamp"])
    else:
        end_time = None  # until end of video
    
    stim_num = int(ev['stim_select'])
    stim = Stim(stim_num)
    suffix = ""
    
    if stim == Stim.PHOTOTAXIS:
        suffix = str(ev['phototaxis_polarity'])
    elif stim == Stim.OMR:
        suffix = str(ev['omr_angle_deg'])
    elif stim == Stim.OKR:
        suffix = str(ev['okr_speed_deg_per_sec'])
    elif stim == Stim.FOLLOWING_LOOMING:
        suffix = str(ev['looming_center_mm'][0])


    out_name = f"stim_{str(stim)}_{suffix}_{stim_counter[stim]}.mp4"
    stim_counter[stim] += 1
    
    cmd = ["ffmpeg", "-y", "-i", video_file, "-ss", str(start_time)]
    if end_time is not None:
        cmd += ["-to", str(end_time)]
    cmd += ["-c", "copy", out_name]
    
    subprocess.run(cmd)

