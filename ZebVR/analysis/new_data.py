import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import os
from scipy import stats
from typing import Tuple
from enum import IntEnum

from ZebVR.protocol import Stim
StimType = Stim.Visual
class Polarity(IntEnum):
    DARKLEFT = -1
    DARKRIGHT = 1
 
DPF = ['7dpf', '8dpf', '9dpf', '10dpf']
PHOTOTAXIS_DURATION_SEC = 1200
TRACKING_FPS = 100
YLIM = (-420,420)


ROOTFOLDER = Path(
    os.environ.get('DATAFOLDER_CICHLIDS', '/media/martin/DATA/Cichlids') 
)
DATAFOLDER = ROOTFOLDER / 'data'
PREPROCFOLDER = ROOTFOLDER / 'preprocessed'
PLOTSFOLDER = ROOTFOLDER / 'plots'

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

# -----------------------------------------------------

def find_stim(stim: pd.DataFrame, tracking: pd.DataFrame, stim_type: StimType) -> pd.DataFrame:
    timestamp = stim.loc[stim.stim_id == stim_type, 'timestamp']
    start = timestamp.iloc[0]
    stop = timestamp.iloc[-1]
    return tracking[(start <= tracking.timestamp) & (tracking.timestamp <= stop)]

def get_heading_angle(data: pd.DataFrame):
    angle = np.arctan2(data.pc1_y, data.pc1_x)
    notna = ~np.isnan(angle)
    angle_unwrapped = np.zeros_like(angle) * np.nan
    angle_unwrapped[notna] = np.unwrap(angle[notna]) # TODO this is probably a bit wrong
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
                usecols=['timestamp', 'pc1_x', 'pc1_y']
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

#------------------------------------------------------------------------------------------
OLD_DATAFILES = [
    #'10_09dpf_Di_27_Aug_2024_17h17min12sec.csv',
    #'11_09dpf_Di_27_Aug_2024_18h47min44sec.csv',
    #'12_09dpf_Di_27_Aug_2024_20h27min13sec.csv',
    #'08_10dpf_Mi_28_Aug_2024_10h18min41sec.csv',
    #'09_10dpf_Mi_28_Aug_2024_11h44min03sec.csv',
    #'10_10dpf_Mi_28_Aug_2024_13h16min25sec.csv',
    #'11_10dpf_Mi_28_Aug_2024_14h30min41sec.csv',
    #'12_10dpf_Mi_28_Aug_2024_16h21min17sec.csv',
    #'13_10dpf_Mi_28_Aug_2024_17h41min49sec.csv', 
    '01_07dpf_Do_29_Aug_2024_09h50min07sec.csv',
    '02_07dpf_Do_29_Aug_2024_11h31min10sec.csv',
    '03_07dpf_Do_29_Aug_2024_13h06min01sec.csv',
    '04_07dpf_Do_29_Aug_2024_14h38min17sec.csv',
    '05_07dpf_Do_29_Aug_2024_16h11min51sec.csv',
    '06_07dpf_Do_29_Aug_2024_17h43min56sec.csv',
    '07_07dpf_Do_29_Aug_2024_19h17min38sec.csv',
    '01_08dpf_Fr_30_Aug_2024_09h26min14sec.csv',
    '02_08dpf_Fr_30_Aug_2024_11h11min11sec.csv',
    '03_08dpf_Fr_30_Aug_2024_12h42min49sec.csv',
    '04_08dpf_Fr_30_Aug_2024_14h15min52sec.csv',
    '05_08dpf_Fr_30_Aug_2024_15h47min53sec.csv',
    '06_08dpf_Fr_30_Aug_2024_17h17min41sec.csv',
    '07_08dpf_Fr_30_Aug_2024_18h48min39sec.csv',
    '02_10dpf_So_01_Sep_2024_11h51min15sec.csv',
    '03_10dpf_So_01_Sep_2024_14h42min31sec.csv',
    '04_10dpf_So_01_Sep_2024_16h12min08sec.csv',
    '05_10dpf_So_01_Sep_2024_17h42min55sec.csv',
    '06_10dpf_So_01_Sep_2024_19h13min20sec.csv',
    '07_10dpf_So_01_Sep_2024_20h44min18sec.csv',
    '14_10dpf_Mo_09_Sep_2024_12h17min25sec.csv',
    '15_10dpf_Mo_09_Sep_2024_13h49min54sec.csv',
    '16_10dpf_Mo_09_Sep_2024_15h24min48sec.csv',
    '17_10dpf_Mo_09_Sep_2024_18h07min58sec.csv',
    '09_07dpf_Di_17_Sep_2024_18h15min51sec.csv',
    '10_07dpf_Di_17_Sep_2024_19h46min28sec.csv',
    '11_07dpf_Di_17_Sep_2024_21h16min13sec.csv',
    '08_08dpf_Mi_18_Sep_2024_10h07min56sec.csv',
    '09_08dpf_Mi_18_Sep_2024_11h43min18sec.csv',
    '10_08dpf_Mi_18_Sep_2024_13h13min31sec.csv',
    '11_08dpf_Mi_18_Sep_2024_14h42min48sec.csv',
    '12_08dpf_Mi_18_Sep_2024_16h14min00sec.csv',
    '13_08dpf_Mi_18_Sep_2024_17h44min33sec.csv',
    '14_08dpf_Mi_18_Sep_2024_19h13min51sec.csv',
    '00_09dpf_Do_19_Sep_2024_10h05min11sec.csv',
    '01_09dpf_Do_19_Sep_2024_11h38min50sec.csv',
    '02_09dpf_Do_19_Sep_2024_13h07min20sec.csv',
    '03_09dpf_Do_19_Sep_2024_14h36min33sec.csv',
    '04_09dpf_Do_19_Sep_2024_16h08min06sec.csv',
    '05_09dpf_Do_19_Sep_2024_17h37min36sec.csv',
    '06_09dpf_Do_19_Sep_2024_19h06min10sec.csv',
    '07_09dpf_Do_19_Sep_2024_20h36min09sec.csv',
    '18_10dpf_Fr_20_Sep_2024_10h39min51sec.csv',
    '19_10dpf_Fr_20_Sep_2024_12h14min45sec.csv',
    '20_10dpf_Fr_20_Sep_2024_13h51min56sec.csv',
    '21_10dpf_Fr_20_Sep_2024_15h23min51sec.csv',
    '22_10dpf_Fr_20_Sep_2024_16h59min47sec.csv',
    '23_10dpf_Fr_20_Sep_2024_18h29min15sec.csv',
    '24_10dpf_Fr_20_Sep_2024_20h02min20sec.csv',
    '12_07dpf_Do_03_Okt_2024_10h58min16sec.csv',
    '13_07dpf_Do_03_Okt_2024_12h28min52sec.csv', 
    '14_07dpf_Do_03_Okt_2024_14h02min07sec.csv', 
    '15_07dpf_Do_03_Okt_2024_15h38min20sec.csv', 
    '16_07dpf_Do_03_Okt_2024_17h07min50sec.csv', 
    '17_07dpf_Do_03_Okt_2024_18h37min36sec.csv'
]

USE_OLD_DATA = True
USE_NEW_DATA = False

def load_data_old(datafile: str) -> pd.DataFrame:
    data = pd.read_csv(
        DATAFOLDER / datafile, 
        usecols=['image_index', 't_local', 'pc1_x', 'pc1_y', 'stim_id', 'phototaxis_polarity']
    )
    data_filtered = data.groupby('image_index').first()
    return data_filtered

def load_data_new(stim_file: str, tracking_file: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    tracking = pd.read_csv(
        DATAFOLDER / tracking_file, 
        usecols=['timestamp', 'pc1_x', 'pc1_y']
    )
    stim = pd.read_csv(
        DATAFOLDER / stim_file, 
        usecols=['timestamp', 'stim_id', 'phototaxis_polarity']
    )
    return stim, tracking

def get_phototaxis_data_new(stim: pd.DataFrame, tracking: pd.DataFrame, polarity: int) -> pd.DataFrame:
    data = stim.loc[stim.stim_id == StimType.PHOTOTAXIS]
    timestamp = data.loc[data.phototaxis_polarity == polarity, 'timestamp']
    start = timestamp.iloc[0]
    stop = timestamp.iloc[-1]
    phototaxis = tracking.loc[(start <= tracking.timestamp) & (tracking.timestamp <= stop)]
    relative_time_sec = get_relative_time_sec(phototaxis)
    angle, angle_unwrapped = get_heading_angle(phototaxis)
    return relative_time_sec, angle_unwrapped

def get_phototaxis_data_old(data: pd.DataFrame, polarity: int) -> pd.DataFrame:
    phototaxis = data.loc[(data.stim_id == StimType.PHOTOTAXIS) & (data.phototaxis_polarity == polarity), ['t_local', 'pc1_x', 'pc1_y']]
    relative_time_sec = phototaxis['t_local'] - phototaxis['t_local'].iloc[0]
    angle, angle_unwrapped = get_heading_angle(phototaxis)
    return relative_time_sec, angle_unwrapped

def get_interpolated_angle_new(stim, tracking, interp_time, polarity):
    relative_time_sec, angle_unwrapped = get_phototaxis_data_new(stim, tracking, polarity)
    angle_unwrapped_interp = np.interp(
        interp_time, 
        relative_time_sec, 
        angle_unwrapped,
        right = np.nan
    )
    return angle_unwrapped_interp
    
def get_interpolated_angle_old(data, interp_time, polarity):
    relative_time_sec, angle_unwrapped = get_phototaxis_data_old(data, polarity)
    angle_unwrapped_interp = np.interp(
        interp_time, 
        relative_time_sec, 
        angle_unwrapped,
        right = np.nan
    )
    return angle_unwrapped_interp

def collect_data(interp_time, dpf):

    phototaxis_darkleft = np.zeros((0,120_000)) * np.nan
    phototaxis_darkright = np.zeros((0,120_000)) * np.nan

    if USE_NEW_DATA:

        for stim_file, tracking_file in DATAFILES:
            if dpf in stim_file:

                print(stim_file, tracking_file)
                stim, tracking = load_data_new(stim_file, tracking_file)

                phototaxis_darkleft = np.vstack((
                    phototaxis_darkleft, 
                    get_interpolated_angle_new(stim, tracking, interp_time, Polarity.DARKLEFT)
                ))
                phototaxis_darkright = np.vstack((
                    phototaxis_darkright, 
                    get_interpolated_angle_new(stim, tracking, interp_time, Polarity.DARKRIGHT)
                ))

    if USE_OLD_DATA:

        for file in OLD_DATAFILES:
            if dpf in file:

                print(file)
                data = load_data_old(file)
                phototaxis_darkleft = np.vstack((
                    phototaxis_darkleft, 
                    get_interpolated_angle_old(data, interp_time, Polarity.DARKLEFT)
                ))
                phototaxis_darkright = np.vstack((
                    phototaxis_darkright, 
                    get_interpolated_angle_old(data, interp_time, Polarity.DARKRIGHT)
                ))

    return phototaxis_darkleft, phototaxis_darkright

interp_time = np.linspace(0, 1200, 120_000)

for dpf in DPF:
    phototaxis_darkleft, phototaxis_darkright = collect_data(interp_time, dpf)
    np.save(
        PREPROCFOLDER / f'phototaxis_darkleft_{dpf}.npy',
        phototaxis_darkleft
    )
    np.save(
        PREPROCFOLDER / f'phototaxis_darkright_{dpf}.npy',
        phototaxis_darkright
    )

for dpf in DPF:

    phototaxis_darkleft = np.load(PREPROCFOLDER / f'phototaxis_darkleft_{dpf}.npy')
    phototaxis_darkright = np.load(PREPROCFOLDER / f'phototaxis_darkright_{dpf}.npy')
    
    avg_darkleft = np.nanmean(phototaxis_darkleft, axis=0)
    avg_darkright = np.nanmean(phototaxis_darkright, axis=0)

    fig = plt.figure()
    ax1 = fig.add_subplot(111) 
    for i in range(phototaxis_darkleft.shape[0]):
        plt.plot(interpolated_time, phototaxis_darkleft[i,:], color='orange', alpha=0.2)
    plt.plot(interpolated_time, avg_darkleft, color='orange', linewidth=2)
    for i in range(phototaxis_darkright.shape[0]):
        plt.plot(interpolated_time, phototaxis_darkright[i,:], color='blue', alpha=0.2)
    plt.plot(interpolated_time, avg_darkright, color='blue', linewidth=2)
    plt.title(dpf)
    plt.xlabel('time (sec)')
    plt.ylabel('cum. angle (rad)')
    plt.show(block = False)
    plt.savefig(PLOTSFOLDER /f'phototaxis_{dpf}')

