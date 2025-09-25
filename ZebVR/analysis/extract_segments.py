import json
import pandas as pd
import subprocess
from enum import IntEnum

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
        
# Load timestamp mapping
ts_df = pd.read_csv("00_07dpf_TLN_Wed_17_Sep_2025_14h37min15sec.csv", sep=",")

# Load stim events
events = []
with open("stim_00_07dpf_TLN_Wed_17_Sep_2025_14h37min32sec.json") as f:
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


    out_name = f"stim_{str(stim)}_{suffix}_{stim_counter[stim]}.mp4"
    stim_counter[stim] += 1
    
    cmd = ["ffmpeg", "-i", "00_07dpf_TLN_Wed_17_Sep_2025_14h37min15sec.mp4", "-ss", str(start_time)]
    if end_time is not None:
        cmd += ["-to", str(end_time)]
    cmd += ["-c", "copy", out_name]
    
    subprocess.run(cmd)

