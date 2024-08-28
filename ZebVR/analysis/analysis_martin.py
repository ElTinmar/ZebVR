import matplotlib.patches
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from typing import Tuple, Dict
from datetime import datetime
import re 
from enum import IntEnum
import seaborn as sns
from scipy.stats import ranksums

class StimType(IntEnum):
    DARK = 0
    BRIGHT = 1
    PHOTOTAXIS = 2
    OMR = 3
    OKR = 4
    LOOMING = 5

# # experiment computer has locale set to german -_-
import locale
import contextlib
@contextlib.contextmanager
def setlocale(*args, **kw):
    saved = locale.setlocale(locale.LC_ALL)
    yield locale.setlocale(*args, **kw)
    locale.setlocale(locale.LC_ALL, saved)

#TODO add legends and labels
# compare cumulative stuff at the last point in time

## Visualization of the results --------------------------------------------------------------------
DATAFILES = [
    '01_09dpf_Di_27_Aug_2024_14h50min47sec.csv',
    '02_09dpf_Di_27_Aug_2024_16h03min14sec.csv',
    '03_09dpf_Di_27_Aug_2024_17h17min12sec.csv',
    '04_09dpf_Di_27_Aug_2024_18h47min44sec.csv',
    '05_09dpf_Di_27_Aug_2024_20h27min13sec.csv'
]

def ranksum_plot(summary: Dict, col = ['red', 'blue']):

    keys = list(summary.keys())

    if len(keys) != 2:
        RuntimeError('Provide dict with two keys')
    
    # plot summary
    stat, p_value = ranksums(summary[keys[0]], summary[keys[1]])

    if p_value < 0.001:
        significance = '***'
    elif p_value < 0.01:
        significance = '**'
    elif p_value < 0.05:
        significance = '*'
    else:
        significance = 'ns'  

    df = pd.DataFrame(summary)
    df_melted = df.melt(var_name='cat', value_name='val')

    fig = plt.figure()
    ax = sns.stripplot(
        data=df_melted, x='cat', y='val', hue='cat',
        alpha=.5, legend=False, palette=sns.color_palette(col)
    )
    sns.pointplot(
        data=df_melted, x='cat', y="val", hue='cat',
        linestyle="none", errorbar=None,
        marker="_", markersize=20, markeredgewidth=3,
        palette=sns.color_palette(col)
    )

    M = max(df_melted['val'])
    plt.plot([0, 1], [M * 1.1] * 2, color='black', lw=1)
    plt.plot([0, 0], [M * 1.05, M * 1.1], color='black', lw=1)
    plt.plot([1, 1], [M * 1.05, M * 1.1], color='black', lw=1)
    plt.text(
        0.5, M * 1.15, 
        f'{significance}', 
        horizontalalignment='center', 
        fontsize=12
    )
    bottom, top = ax.get_ylim()
    ax.set_ylim(bottom, M * 1.2)
    ax.set_xlim(-0.5, 1.5)
    plt.show()

def parse_filename(filename: str, loc: str = 'de_DE.utf8') -> Tuple:

    regexp = re.compile(r"""
        (?P<fish_id>\d+)_
        (?P<dpf>\d+)dpf_
        (?P<datetime>\w+).csv
        """, re.VERBOSE)

    match = regexp.fullmatch(filename)
    if match is None:
        raise RuntimeError(f'Wrong filename format, {filename}')
    
    fish_id = int(match.group('fish_id'))
    dpf = int(match.group('dpf'))
    
    with setlocale(locale.LC_ALL, loc):
        date = datetime.strptime(match.group('datetime'),'%a_%d_%b_%Y_%Hh%Mmin%Ssec')
    
    return (fish_id, dpf, date)

def get_n_tail_pts(data):
    header = data.columns
    tail_points = [t for t in header if "tail_point" in t]
    return int(len(tail_points)/2)
    
def tail_skeleton_to_angles(tail_skeleton):
    tail_vectors = tail_skeleton[:,1:] - tail_skeleton[:,:-1] 
    angles = np.arctan2(tail_vectors[1,:], tail_vectors[0,:]) 
    return angles

def get_tail(panda_series,n_tail_pts):
    tail_skeleton = np.array([
        [panda_series[f'tail_point_{n:03d}_x'] for n in range(n_tail_pts)],
        [panda_series[f'tail_point_{n:03d}_y'] for n in range(n_tail_pts)]
    ])
    tail_angle = tail_skeleton_to_angles(tail_skeleton)
    return tail_skeleton, tail_angle

def get_heading_angle(data):
    angle = np.arctan2(data['pc1_y'],data['pc1_x'])
    angle_unwrapped = np.unwrap(angle) 
    return angle, angle_unwrapped

def get_relative_time(data):
    return data['t_local'] - data['t_local'].iloc[0]

def get_distance(data):
    x_diff = data['centroid_x'].diff()
    y_diff = data['centroid_y'].diff()
    distance = np.sqrt(x_diff**2+y_diff**2)
    return distance

def analyse_phototaxis(data, fish_id, dpf):
    phototaxis = data[data['stim_id'] == StimType.PHOTOTAXIS]

    def get_data(polarity):
        pol = phototaxis[phototaxis['phototaxis_polarity'] == polarity]
        time = get_relative_time(pol)
        angle, angle_unwrapped = get_heading_angle(pol)
        res = pd.DataFrame({
            'time': time, 
            'angle': angle, 
            'angle_unwrapped': angle_unwrapped,
            'polarity': polarity,
            'fish_id': fish_id,
            'dpf': dpf
        })
        return res

    res = pd.concat((get_data(1),get_data(-1)))
    return res

def analyse_dark_vs_bright(data, fish_id, dpf):

    def get_data(stim_type):
        light = data[data['stim_id'] == stim_type]
        res = pd.DataFrame({
            'time': get_relative_time(light), 
            'distance':  get_distance(light),
            'condition': stim_type,
            'fish_id': fish_id,
            'dpf': dpf
        })
        return res
    
    res = pd.concat((
        get_data(StimType.BRIGHT),
        get_data(StimType.DARK)
    ))
    return res

def analyse_omr(data, fish_id, dpf):
    omr = data[data['stim_id'] == StimType.OMR]

    def get_data(omr_angle):
        ang = omr[omr['omr_angle_deg'] == omr_angle]
        angle, angle_unwrapped = get_heading_angle(ang)
        res = pd.DataFrame({
            'time': get_relative_time(ang), 
            'angle': angle, 
            'angle_unwrapped': angle_unwrapped,
            'distance':  get_distance(ang),
            'omr_angle': omr_angle,
            'fish_id': fish_id,
            'dpf': dpf
        })
        return res
    
    res = pd.concat((
        get_data(0.0),
        get_data(90.0),
        get_data(-90.0),
        get_data(180.0),
    ))
    return res

def analyse_okr(data, fish_id, dpf):
    okr = data[data['stim_id'] == StimType.OKR]
    
    def get_data(okr_angle):
        ang = okr[okr['okr_speed_deg_per_sec'] == okr_angle]
        time = get_relative_time(ang)
        angle, angle_unwrapped = get_heading_angle(ang)
        res = pd.DataFrame({
            'time': time, 
            'angle': angle, 
            'angle_unwrapped': angle_unwrapped,
            'left_eye_angle': ang['left_eye_angle'],
            'right_eye_angle': ang['right_eye_angle'],
            'okr_angle': okr_angle,
            'fish_id': fish_id,
            'dpf': dpf
        })
        return res

    res = pd.concat((
        get_data(36.0),
        get_data(-36.0)
    ))
    return res

def analyse_looming(data, fish_id, dpf):
    looming = data[data['stim_id'] == StimType.LOOMING]
    rel_time =  looming['t_local'] % looming['looming_period_sec']
    looming_on =  rel_time <= looming['looming_expansion_time_sec']


def plot_dark_vs_bright(data):

    for dpf, data_dpf in data.groupby('dpf'):

        summary = {}
        summary[StimType.BRIGHT] = []
        summary[StimType.DARK] = []

        fig = plt.figure()
        fig.suptitle(f'{dpf} dpf')

        # plot trajectory
        for fish_id, data_fish in data_dpf.groupby('fish_id'):
            for light, data_light in data_fish.groupby('condition'):
                cum_distance = data_light['distance'].cumsum()
                plt.plot(
                    data_light['time'], 
                    cum_distance, 
                    color='r' if light == StimType.BRIGHT else 'b' if light==StimType.DARK else 'k',
                    marker ='o',
                    markevery=[-1]
                )
                summary[light].append(cum_distance.iloc[-1])
        plt.show()

        ranksum_plot(summary)

def plot_omr_left_vs_right(data):

    for dpf, data_dpf in data.groupby('dpf'):

        summary = {}
        summary[-90.0] = []
        summary[90] = []

        fig = plt.figure()
        fig.suptitle(f'{dpf} dpf')

        for fish_id, data_fish in data_dpf.groupby('fish_id'):
            for omr_angle, data_omr in data_fish.groupby('omr_angle'):
                if omr_angle in [-90.0,90.0]:
                    angle_unwrapped = data_omr['angle_unwrapped']
                    plt.plot(
                        angle_unwrapped, 
                        data_omr['time'], 
                        color='r' if omr_angle==90 else 'b' if omr_angle==-90 else 'k',
                        marker ='o',
                        markevery=[-1]
                    )
                    summary[omr_angle].append(angle_unwrapped.iloc[-1])
        plt.show()

        ranksum_plot(summary)

def plot_omr_back_vs_front(data):
    
    for dpf, data_dpf in data.groupby('dpf'):

        summary = {}
        summary[0.0] = []
        summary[180.0] = []

        fig = plt.figure()
        fig.suptitle(f'{dpf} dpf')

        for fish_id, data_fish in data_dpf.groupby('fish_id'):
            for omr_angle, data_omr in data_fish.groupby('omr_angle'):
                if omr_angle in [0.0,180.0]:
                    cum_distance = data_omr['distance'].cumsum()
                    plt.plot(
                        data_omr['time'], 
                        cum_distance, 
                        color='r' if omr_angle==0.0 else 'b' if omr_angle==180.0 else 'k',
                        marker ='o',
                        markevery=[-1]
                    )
                    summary[omr_angle].append(cum_distance.iloc[-1])
        plt.show()

        ranksum_plot(summary)

def plot_okr_eyes(data):

    for dpf, data_dpf in data.groupby('dpf'):
        for fish_id, data_fish in data_dpf.groupby('fish_id'):
            fig, ax = plt.subplots(2)
            for okr_angle, data_okr in data_fish.groupby('okr_angle'):
                ax_id = 0 if okr_angle == 36 else 1
                ax[ax_id].plot(
                    data_okr['time'], 
                    data_okr['left_eye_angle'], 
                    color='b'
                )
                ax[ax_id].plot(
                    data_okr['time'], 
                    data_okr['right_eye_angle'], 
                    color='r'
                )
        plt.show()

def plot_okr_turns(data):

    for dpf, data_dpf in data.groupby('dpf'):

        summary = {}
        summary[36.0] = []
        summary[-36.0] = []

        fig = plt.figure()
        fig.suptitle(f'{dpf} dpf')

        for fish_id, data_fish in data_dpf.groupby('fish_id'):
            for okr_angle, data_omr in data_fish.groupby('okr_angle'):
                angle_unwrapped = data_omr['angle_unwrapped']
                plt.plot(
                    angle_unwrapped, 
                    data_omr['time'], 
                    color='r' if okr_angle==36 else 'b' if okr_angle==-36 else 'k',
                    marker ='o',
                    markevery=[-1]
                )
                summary[okr_angle].append(angle_unwrapped.iloc[-1])
        plt.show()

        ranksum_plot(summary)

def plot_phototaxis(data):

    for dpf, data_dpf in data.groupby('dpf'):

        summary = {}
        summary[1] = []
        summary[-1] = []

        fig = plt.figure()
        fig.suptitle(f'{dpf} dpf')

        for fish_id, data_fish in data_dpf.groupby('fish_id'):
            for polarity, data_polarity in data_fish.groupby('polarity'):
                angle_unwrapped = data_polarity['angle_unwrapped']
                plt.plot(
                    data_polarity['angle_unwrapped'], 
                    data_polarity['time'], 
                    color='r' if polarity==1 else 'b',
                    marker ='o',
                    markevery=[-1]
                )
                summary[polarity].append(angle_unwrapped.iloc[-1])
        plt.show()

        ranksum_plot(summary)

def plot_loomings(data):
    pass

phototaxis = pd.DataFrame()
omr = pd.DataFrame()
okr = pd.DataFrame()
bright_vs_dark = pd.DataFrame()
looming = pd.DataFrame()

for file in DATAFILES:

    print(file)
    fish_id, dpf, date = parse_filename(file)
    data = pd.read_csv(file)
    data_filtered = data.groupby('image_index').first()
    data_filtered = data_filtered[1:]
    data_filtered['stim_id'] = data_filtered['stim_id'].astype(int)
    
    bright_vs_dark = pd.concat((
        bright_vs_dark,
        analyse_dark_vs_bright(data_filtered, fish_id, dpf)
    ))

    phototaxis = pd.concat((
        phototaxis, 
        analyse_phototaxis(data_filtered, fish_id, dpf)
    ))

    omr = pd.concat((
        omr, 
        analyse_omr(data_filtered, fish_id, dpf)
    ))

    okr = pd.concat((
        okr,
        analyse_okr(data_filtered, fish_id, dpf)
    ))

    looming = pd.concat((
        looming,
        analyse_looming(data_filtered, fish_id, dpf)
    ))

plot_dark_vs_bright(bright_vs_dark)
plot_phototaxis(phototaxis)
plot_omr_left_vs_right(omr)
plot_omr_back_vs_front(omr)
plot_okr_eyes(okr)
plot_okr_turns(okr)
plot_loomings(looming)


