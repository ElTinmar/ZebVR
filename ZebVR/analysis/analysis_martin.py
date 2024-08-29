import matplotlib.patches
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from typing import Tuple, Dict, Iterable
from datetime import datetime
import re 
from enum import IntEnum
import seaborn as sns
from scipy.stats import ranksums
from ZebVR.config import (
    PIX_PER_MM,
    CAM_WIDTH,
    CAM_HEIGHT
)

matplotlib.rcParams['font.size'] = 12

class StimType(IntEnum):
    DARK = 0
    BRIGHT = 1
    PHOTOTAXIS = 2
    OMR = 3
    OKR = 4
    LOOMING = 5

COLORS = ('#FF6900', '#002BFF')
ARENA_DIAMETER_MM = 50
ARENA_DIAMETER_PX = PIX_PER_MM * ARENA_DIAMETER_MM
ARENA_CENTER = (1037, 1165)

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
    '05_09dpf_Di_27_Aug_2024_20h27min13sec.csv',
    '01_10dpf_Mi_28_Aug_2024_10h18min41sec.csv',
    '02_10dpf_Mi_28_Aug_2024_11h44min03sec.csv',
    '03_10dpf_Mi_28_Aug_2024_13h16min25sec.csv',
    '04_10dpf_Mi_28_Aug_2024_14h30min41sec.csv',
    '05_10dpf_Mi_28_Aug_2024_16h21min17sec.csv',
    '06_10dpf_Mi_28_Aug_2024_17h41min49sec.csv'
]

def asterisk(p_value: float) -> str:

    if p_value < 0.0001:
        significance = '****'
    elif p_value < 0.001:
        significance = '***'
    elif p_value < 0.01:
        significance = '**'
    elif p_value < 0.05:
        significance = '*'
    else:
        significance = 'ns' 

    return significance

def significance_bridge(ax,x,y,p_value,fontsize,prct_offset=0.05):

    bottom, top = ax.get_ylim()
    height = top-bottom
    offset = prct_offset * height

    Mx = np.nanmax(x) + 1.5 * offset
    My = np.nanmax(y) + 1.5 * offset
    Mxy = np.nanmax((Mx,My)) + offset
    plt.plot([0, 0, 1, 1], [Mx, Mxy, Mxy, My], color='#555555', lw=1.5)

    significance = asterisk(p_value)
    plt.text(
        0.5, Mxy + offset, 
        f'{significance}', 
        horizontalalignment='center', 
        fontsize=fontsize
    )
    
    ax.set_ylim(bottom, Mxy + 3*offset)

def ranksum_plot(
        x, 
        y, 
        cat_names: Iterable, 
        ylabel: str, 
        title: str,
        col: Iterable, 
        fontsize: int = 12, 
        *args, 
        **kwargs):
        
    stat, p_value = ranksums(x, y, nan_policy='omit', *args, **kwargs)

    df = pd.DataFrame({cat_names[0]: x, cat_names[1]: y})
    df_melted = df.melt(var_name='cat', value_name='val')

    fig = plt.figure()
    fig.suptitle(title)

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
    ax.set_xlim(-0.5, 1.5)
    ax.set_ylabel(ylabel)
    ax.set_xlabel('')
    ax.set_box_aspect(1)

    significance_bridge(ax,x,y,p_value,fontsize)

    fig.tight_layout()

    plt.show(block=False)

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
    notna = ~np.isnan(angle)
    angle_unwrapped = np.zeros_like(angle) * np.nan
    angle_unwrapped[notna] = np.unwrap(angle[notna]) # TODO this is probably a bit wrong
    return angle, angle_unwrapped

def get_relative_time(data):
    return data['t_local'] - data['t_local'].iloc[0]

def get_distance(data):
    x_diff = data['centroid_x'].diff()
    y_diff = data['centroid_y'].diff()
    distance = np.sqrt(x_diff**2+y_diff**2)
    return distance

def correct_spurious_flips(data):
    # correct tracking errror where the body axis is flipped 180 deg
    pass 

def remove_data_on_well_edges(data, threshold_radius_mm = 22.5):

    threshold_radius_px = PIX_PER_MM * threshold_radius_mm
    x,y = np.mgrid[0:CAM_WIDTH:10,0:CAM_HEIGHT:10]
    circle = (x - ARENA_CENTER[0])**2 + (y - ARENA_CENTER[0])**2 <= threshold_radius_px**2 
    ind_edges = (data['centroid_x']-ARENA_CENTER[0])**2 + (data['centroid_y']-ARENA_CENTER[0])**2 >= threshold_radius_px**2 

    fig = plt.figure()
    plt.plot(data['centroid_x'],data['centroid_y'])
    plt.plot(x[circle],y[circle], 'or', alpha = 0.05)
    plt.axis('square')
    plt.show()

    # I don't want to compute heading based properties (e.g turns) on the wall
    data.loc[ind_edges, ['pc1_x','pc1_y','pc2_x','pc2_y']] = pd.NA

    return data

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
                valid = cum_distance.notna()
                plt.plot(
                    data_light.loc[valid, 'time'], 
                    cum_distance[valid], 
                    color = COLORS[0] if light == StimType.BRIGHT else COLORS[1] if light==StimType.DARK else 'k',
                    marker ='o',
                    markevery=[-1]
                )
                plt.xlabel('time (s)')
                plt.ylabel('cum. distance (px)')
                summary[light].append(cum_distance[valid].iloc[-1])
        plt.show(block=False)

        ranksum_plot(
            x = summary[StimType.BRIGHT], 
            y = summary[StimType.DARK],
            cat_names=('bright', 'dark'),
            ylabel='cum. distance (px)',
            title=f'{dpf} dpf',
            col=COLORS
        )

def plot_omr_left_vs_right(data):

    for dpf, data_dpf in data.groupby('dpf'):

        summary = {}
        summary[-90] = []
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
                        color=COLORS[0] if omr_angle==90 else COLORS[1] if omr_angle==-90 else 'k',
                        marker ='o',
                        markevery=[-1]
                    )
                    plt.xlabel('cumulative angle (rad)')
                    plt.ylabel('time (s)')
                    summary[omr_angle].append(angle_unwrapped.iloc[-1])

        plt.show(block=False)

        ranksum_plot(
            x = summary[90], 
            y = summary[-90],
            cat_names=('leftward', 'rightward'),
            ylabel='cum. angle (rad)',
            title=f'{dpf} dpf',
            col=COLORS
        )

def plot_omr_back_vs_front(data):
    
    for dpf, data_dpf in data.groupby('dpf'):

        summary = {}
        summary[0] = []
        summary[180] = []

        fig = plt.figure()
        fig.suptitle(f'{dpf} dpf')

        for fish_id, data_fish in data_dpf.groupby('fish_id'):
            for omr_angle, data_omr in data_fish.groupby('omr_angle'):
                if omr_angle in [0.0,180.0]:
                    cum_distance = data_omr['distance'].cumsum()
                    plt.plot(
                        data_omr['time'], 
                        cum_distance, 
                        color=COLORS[0] if omr_angle==0 else COLORS[1] if omr_angle==180 else 'k',
                        marker ='o',
                        markevery=[-1]
                    )
                    plt.xlabel('time (s)')
                    plt.ylabel('cum. distance (px)')
                    summary[omr_angle].append(cum_distance.iloc[-1])

        plt.show(block=False)

        ranksum_plot(
            x = summary[0], 
            y = summary[180],
            cat_names=('backward', 'forward'),
            ylabel='cum. distance (px)',
            title=f'{dpf} dpf',
            col=COLORS
        )

def plot_okr_eyes(data):

    for dpf, data_dpf in data.groupby('dpf'):
        for fish_id, data_fish in data_dpf.groupby('fish_id'):
            fig, ax = plt.subplots(2)
            for okr_angle, data_okr in data_fish.groupby('okr_angle'):
                ax_id = 0 if okr_angle == 36 else 1
                ax[ax_id].plot(
                    data_okr['time'], 
                    data_okr['left_eye_angle'], 
                    color=COLORS[0]
                )
                ax[ax_id].plot(
                    data_okr['time'], 
                    data_okr['right_eye_angle'], 
                    color=COLORS[1]
                )
        plt.show(block=False)

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
                    color=COLORS[0] if okr_angle==36 else COLORS[1] if okr_angle==-36 else 'k',
                    marker ='o',
                    markevery=[-1]
                )
                plt.xlabel('cumulative angle (rad)')
                plt.ylabel('time (s)')
                summary[okr_angle].append(angle_unwrapped.iloc[-1])

        plt.show(block=False)

        ranksum_plot(
            x = summary[36], 
            y = summary[-36],
            cat_names=('clockwise', 'counterclockwise'),
            ylabel='cum. angle (rad)',
            title=f'{dpf} dpf',
            col=COLORS
        )

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
                valid = angle_unwrapped.notna()
                plt.plot(
                    angle_unwrapped, 
                    data_polarity['time'], 
                    color=COLORS[0] if polarity==1 else COLORS[1],
                    marker ='o',
                    markevery=[-1]
                )
                plt.xlabel('cumulative angle (rad)')
                plt.ylabel('time (s)')
                if sum(valid) == 0:
                    summary[polarity].append(np.nan)
                else:
                    summary[polarity].append(angle_unwrapped[valid].iloc[-1])

        plt.show(block=False)

        ranksum_plot(
            x = summary[1], 
            y = summary[-1],
            cat_names=('dark-left', 'dark-right'),
            ylabel='cum. angle (rad)',
            title=f'{dpf} dpf',
            col=COLORS
        )

def plot_loomings(data):
    # distance and escape trajectories
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
    #data_filtered = remove_data_on_well_edges(data_filtered)
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


