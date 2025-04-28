import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import os
from scipy import stats

from ZebVR.protocol import Stim
StimType = Stim.Visual

DATAFOLDER = Path(
    os.environ.get('DATAFOLDER_CICHLIDS', '/media/martin/DATA/Cichlids/')
)
DATAFILES = [
    ('stim_00_07dpf_Cichlid_Do_24_Apr_2025_12h00min07sec.csv', 'tracking_00_07dpf_Cichlid_Thu_24_Apr_2025_12h00min07sec.csv'), # bad flipping example
    ('stim_00_08dpf_Cichlid_Fr_25_Apr_2025_11h21min18sec.csv', 'tracking_00_08dpf_Cichlid_Fri_25_Apr_2025_11h21min17sec.csv'),
    ('stim_00_09dpf_Cichlid_Sa_26_Apr_2025_10h25min21sec.csv', 'tracking_00_09dpf_Cichlid_Sat_26_Apr_2025_10h25min20sec.csv'), 
    ('stim_01_07dpf_Cichlid_Do_24_Apr_2025_13h42min37sec.csv', 'tracking_01_07dpf_Cichlid_Thu_24_Apr_2025_13h42min37sec.csv'),
    ('stim_01_08dpf_Cichlid_Fr_25_Apr_2025_12h49min10sec.csv', 'tracking_01_08dpf_Cichlid_Fri_25_Apr_2025_12h49min09sec.csv'),
    ('stim_01_09dpf_Cichlid_Sa_26_Apr_2025_11h53min47sec.csv', 'tracking_01_09dpf_Cichlid_Sat_26_Apr_2025_11h53min46sec.csv'),
    ('stim_02_07dpf_Cichlid_Do_24_Apr_2025_15h04min23sec.csv', 'tracking_02_07dpf_Cichlid_Thu_24_Apr_2025_15h04min23sec.csv'),
    ('stim_02_08dpf_Cichlid_Fr_25_Apr_2025_14h17min23sec.csv', 'tracking_02_08dpf_Cichlid_Fri_25_Apr_2025_14h17min23sec.csv'),
    ('stim_02_09dpf_Cichlid_Sa_26_Apr_2025_12h53min44sec.csv', 'tracking_02_09dpf_Cichlid_Sat_26_Apr_2025_12h53min44sec.csv'),
    ('stim_03_07dpf_Cichlid_Do_24_Apr_2025_16h12min34sec.csv', 'tracking_03_07dpf_Cichlid_Thu_24_Apr_2025_16h12min34sec.csv'),
    ('stim_03_08dpf_Cichlid_Fr_25_Apr_2025_15h19min53sec.csv', 'tracking_03_08dpf_Cichlid_Fri_25_Apr_2025_15h19min52sec.csv'),
    ('stim_03_09dpf_Cichlid_Sa_26_Apr_2025_14h27min00sec.csv', 'tracking_03_09dpf_Cichlid_Sat_26_Apr_2025_14h27min00sec.csv'),
    ('stim_04_08dpf_Cichlid_Fr_25_Apr_2025_16h27min57sec.csv', 'tracking_04_08dpf_Cichlid_Fri_25_Apr_2025_16h27min56sec.csv'),
    ('stim_04_09dpf_Cichlid_Sa_26_Apr_2025_15h42min49sec.csv', 'tracking_04_09dpf_Cichlid_Sat_26_Apr_2025_15h42min49sec.csv'),
    ('stim_05_08dpf_Cichlid_Fr_25_Apr_2025_17h37min00sec.csv', 'tracking_05_08dpf_Cichlid_Fri_25_Apr_2025_17h36min59sec.csv'),
    ('stim_05_09dpf_Cichlid_Sa_26_Apr_2025_16h47min50sec.csv', 'tracking_05_09dpf_Cichlid_Sat_26_Apr_2025_16h47min51sec.csv')
]
DPF = ['7dpf', '8dpf', '9dpf']
PHOTOTAXIS_DURATION_SEC = 1200
TRACKING_FPS = 100
YLIM = (-420,420)

# -----------------------------------------------------

stim_file, tracking_file = DATAFILES[2]

tracking = pd.read_csv(
    DATAFOLDER / tracking_file, 
    usecols=['index', 'timestamp', 'centroid_x', 'centroid_y', 'pc1_x', 'pc1_y']
)
stim = pd.read_csv(
    DATAFOLDER / stim_file, 
    usecols=['timestamp', 'stim_id', 'phototaxis_polarity']
)

def find_stim(stim: pd.DataFrame, tracking: pd.DataFrame, stim_type: StimType) -> pd.DataFrame:
    timestamps_dark = stim.loc[stim['stim_id'] == stim_type, 'timestamp']
    start = timestamps_dark.iloc[0]
    stop = timestamps_dark.iloc[-1]
    return tracking[(start <= tracking.timestamp) & (tracking.timestamp <= stop)]

def get_heading_angle(data: pd.DataFrame):
    angle = np.arctan2(data['pc1_y'],data['pc1_x'])
    angle_unwrapped = np.unwrap(angle)
    return angle, angle_unwrapped 

def get_relative_time_sec(data: pd.DataFrame):
    first_timestamp = data.iloc[0].timestamp
    relative_time_ns = data.timestamp - first_timestamp
    return 1e-9*relative_time_ns

num_frames_phototaxis = 2*PHOTOTAXIS_DURATION_SEC*TRACKING_FPS
interpolated_time = np.linspace(0, 2*PHOTOTAXIS_DURATION_SEC, num_frames_phototaxis)

for age in DPF:

    phototaxis_data = np.zeros((0,num_frames_phototaxis))

    for stim_file, tracking_file in DATAFILES:

        if age in stim_file:
            tracking = pd.read_csv(
                DATAFOLDER / tracking_file, 
                usecols=['index', 'timestamp', 'centroid_x', 'centroid_y', 'pc1_x', 'pc1_y']
            )
            stim = pd.read_csv(
                DATAFOLDER / stim_file, 
                usecols=['timestamp', 'stim_id', 'phototaxis_polarity']
            )
            phototaxis = find_stim(stim, tracking, StimType.PHOTOTAXIS)
            relative_time_sec = get_relative_time_sec(phototaxis)
            angle, angle_unwrapped = get_heading_angle(phototaxis)
            angle_unwrapped_interp = np.interp(interpolated_time, relative_time_sec, angle_unwrapped)
            phototaxis_data = np.vstack((phototaxis_data, angle_unwrapped_interp))
  
    firsthalf = interpolated_time[0:num_frames_phototaxis//2]
    secondhalf = interpolated_time[num_frames_phototaxis//2:-1]
    avg_firsthalf = np.mean(phototaxis_data, axis=0)[0:num_frames_phototaxis//2]
    avg_secondhalf = np.mean(phototaxis_data, axis=0)[num_frames_phototaxis//2:-1]

    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1) 
    for i in range(phototaxis_data.shape[0]):
        plt.plot(interpolated_time, phototaxis_data[i,:], color='gray', alpha=0.2)
    plt.plot(firsthalf, avg_firsthalf, color='blue', linewidth=2)
    plt.plot(secondhalf, avg_secondhalf - avg_secondhalf[0], color='orange', linewidth=2)
    plt.title(age)
    plt.xlabel('time (sec)')
    plt.ylabel('cum. angle (rad)')

    plt.ylim(*YLIM)
    ax.add_patch(plt.Rectangle((0,0), 1200, YLIM[1], color='#333333'))
    ax.add_patch(plt.Rectangle((1200,0), 1200, YLIM[0], color='#333333'))
    plt.show(block=False)
