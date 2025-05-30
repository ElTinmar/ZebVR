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
import os
from pathlib import Path

PIX_PER_MM = 38.773681409813456
CAM_WIDTH = 2048
CAM_HEIGHT = 2048

matplotlib.rcParams['font.size'] = 12

# TODO ---------------------
# check for jumping centroid
# check for jumping heading
# -> remove offending data
# 
# IDEAS: 
#   - wavelet transform to identify high freq jumping? 
#   - speed threshold  

# TODO ---------------------
# Better plotting with images

# NOTE ---------------------
# For the 9 dpfs of Sa_31_Aug_2024, the cold
# mirror was likely off. Maybe discard non
# global stimuli

# NOTE ---------------------
# Resolve the 300/600s phototaxis 
# duration discrepancy for ranksum tests 
# (maybe just remove data acquired @ 300s, 
# only for phototaxis though, the ohers are 
# fine)

## NOTE --------------------
# Top projection / Bottom recording: 
#   + angles = fish turns to its left 
#   - angles = fish turns to its right

class StimType(IntEnum):
    DARK = 0
    BRIGHT = 1
    PHOTOTAXIS = 2
    OMR = 3
    OKR = 4
    LOOMING = 5

COLORS = ('#FF6900', '#002BFF')

ARENA_CENTER = (1049,1049)
ARENA_DIAMETER_MM = 50
ARENA_DIAMETER_PX = PIX_PER_MM * ARENA_DIAMETER_MM
BASE_FOLDER = Path('output')
DATA_FOLDER = BASE_FOLDER / 'data'
#DATA_FOLDER = '/media/martin/DATA/Cichlids'
RESULT_FOLDER = BASE_FOLDER / 'results'

## experiment computer has locale set to german -_-
import locale
import contextlib
@contextlib.contextmanager
def setlocale(*args, **kw):
    saved = locale.setlocale(locale.LC_ALL)
    yield locale.setlocale(*args, **kw)
    locale.setlocale(locale.LC_ALL, saved)


## Visualization of the results --------------------------------------------------------------------

# Excluded because of potentially bad resgistration
#'01_09dpf_Sa_31_Aug_2024_09h34min08sec.csv',
#'02_09dpf_Sa_31_Aug_2024_11h06min41sec.csv',
#'03_09dpf_Sa_31_Aug_2024_12h40min20sec.csv',
#'04_09dpf_Sa_31_Aug_2024_14h14min07sec.csv',
#'05_09dpf_Sa_31_Aug_2024_15h57min07sec.csv',
#'06_09dpf_Sa_31_Aug_2024_17h28min16sec.csv',
#'07_09dpf_Sa_31_Aug_2024_19h00min21sec.csv',
#'01_10dpf_So_01_Sep_2024_09h18min10sec.csv',

# exclude because of bad tracking
# '08_07dpf_Di_17_Sep_2024_16h43min16sec.csv',
# '08_09dpf_Di_27_Aug_2024_14h50min47sec.csv', 
# '09_09dpf_Di_27_Aug_2024_16h03min14sec.csv',

# exclude from phototaxis because I changed duration
# other assays are still usable
EXCLUDE_PHOTOTAXIS = [
    '10_09dpf_Di_27_Aug_2024_17h17min12sec.csv', # exclude shorter trial
    '11_09dpf_Di_27_Aug_2024_18h47min44sec.csv', # exclude shorter trial
    '12_09dpf_Di_27_Aug_2024_20h27min13sec.csv', # exclude shorter trial
    '08_10dpf_Mi_28_Aug_2024_10h18min41sec.csv', # exclude shorter trial
    '09_10dpf_Mi_28_Aug_2024_11h44min03sec.csv', # exclude shorter trial
    '10_10dpf_Mi_28_Aug_2024_13h16min25sec.csv', # exclude shorter trial
    '11_10dpf_Mi_28_Aug_2024_14h30min41sec.csv', # exclude shorter trial
    '12_10dpf_Mi_28_Aug_2024_16h21min17sec.csv', # exclude shorter trial
    '13_10dpf_Mi_28_Aug_2024_17h41min49sec.csv', # exclude shorter trial
]

DATAFILES = [
    '10_09dpf_Di_27_Aug_2024_17h17min12sec.csv',
    '11_09dpf_Di_27_Aug_2024_18h47min44sec.csv',
    '12_09dpf_Di_27_Aug_2024_20h27min13sec.csv',
    '08_10dpf_Mi_28_Aug_2024_10h18min41sec.csv',
    '09_10dpf_Mi_28_Aug_2024_11h44min03sec.csv',
    '10_10dpf_Mi_28_Aug_2024_13h16min25sec.csv',
    '11_10dpf_Mi_28_Aug_2024_14h30min41sec.csv',
    '12_10dpf_Mi_28_Aug_2024_16h21min17sec.csv',
    '13_10dpf_Mi_28_Aug_2024_17h41min49sec.csv', 
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
    ax.plot([0, 0, 1, 1], [Mx, Mxy, Mxy, My], color='#555555', lw=1.5)

    significance = asterisk(p_value)
    ax.text(
        0.5, Mxy + offset, 
        f'{significance}', 
        horizontalalignment='center', 
        fontsize=fontsize
    )
    
    ax.set_ylim(bottom, Mxy + 3*offset)

def ranksum_plot(
        ax,
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

    ax.set_title(title)

    sns.stripplot(ax = ax,
        data=df_melted, x='cat', y='val', hue='cat',
        alpha=.5, legend=False, palette=sns.color_palette(col),
        s=7.5
    )
    sns.pointplot(
        ax = ax,
        data=df_melted, x='cat', y="val", hue='cat',
        linestyle="none", errorbar=None,
        marker="_", markersize=30, markeredgewidth=3,
        palette=sns.color_palette(col)
    )
    ax.set_xlim(-0.5, 1.5)
    ax.set_ylabel(ylabel)
    ax.set_xlabel('')
    ax.set_box_aspect(1)

    significance_bridge(ax,x,y,p_value,fontsize)

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

def get_relative_index(data):
    return data.index - data.index[0]

def get_distance(data):
    x_diff = data['centroid_x'].diff()
    y_diff = data['centroid_y'].diff()
    distance = np.sqrt(x_diff**2+y_diff**2)
    return distance * 1/PIX_PER_MM

def correct_spurious_flips(data):
    # correct tracking errror where the body axis is flipped 180 deg
    pass 

def remove_data_on_well_edges(data, threshold_radius_mm = 22.5):

    '''
    # Some fish don't explore the whole arena. This does not work
    mx = data.loc[data['centroid_x']>0, 'centroid_x'].min()
    Mx = data['centroid_x'].max()
    my = data.loc[data['centroid_y']>0, 'centroid_y'].min()
    My = data['centroid_y'].max()
    center_x = .5*(mx+Mx) 
    center_y = .5*(my+My) 
    '''

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
        res = res.set_index(get_relative_index(pol))
        return res

    res = pd.concat((get_data(1),get_data(-1)))
    return res

def analyse_dark_vs_bright(data, fish_id, dpf):

    def get_data(stim_type):
        light = data[data['stim_id'] == stim_type]
        res = pd.DataFrame({
            'time': get_relative_time(light), 
            'cum_distance':  get_distance(light).cumsum(),
            'light_condition': stim_type,
            'fish_id': fish_id,
            'dpf': dpf
        })
        res = res.set_index(get_relative_index(light))
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
            'cum_distance':  get_distance(ang).cumsum(),
            'omr_angle': omr_angle,
            'fish_id': fish_id,
            'dpf': dpf
        })
        res = res.set_index(get_relative_index(ang))
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
        res = res.set_index(get_relative_index(ang))
        return res

    res = pd.concat((
        get_data(36.0),
        get_data(-36.0)
    ))
    return res

def analyse_looming(data, fish_id, dpf):
    looming = data[data['stim_id'] == StimType.LOOMING]
    rel_time =  looming['t_local'] % looming['looming_period_sec']
    looming_on = rel_time <= looming['looming_expansion_time_sec']
    angle, angle_unwrapped = get_heading_angle(looming)
    res =  pd.DataFrame({
        'time': get_relative_time(looming), 
        'angle': angle, 
        'looming_on': looming_on,
        'distance':  get_distance(looming),
        'centroid_x': looming['centroid_x'],
        'centroid_y': looming['centroid_y'],
        'fish_id': fish_id,
        'dpf': dpf
    })
    res = res.set_index(get_relative_index(looming))
    return res


def plot_helper(
        data: pd.DataFrame, 
        cat: str, 
        val: str, 
        keys: Iterable, 
        key_names: Iterable, 
        col: Iterable, 
        xlabel:str, 
        vertical_time_axis: bool,
        prefix: str,
        end_idx: int = -1
    ):

    fig, axs = plt.subplots(2, 4, figsize=(15,7.5))

    count = 0

    for dpf, data_dpf in data.groupby('dpf'):
            
        axs[0, count].set_title(f'{dpf} dpf')

        summary = {}
        for i, k in enumerate(keys):
            summary[k] = []

            df = data_dpf[data_dpf[cat] == k]
            df.loc[:, 'time'] = pd.to_datetime(df['time'], unit='s')
            df = df.set_index('time')
            df = df.sort_index()
            df = df.pivot(columns='fish_id', values=val)
            df = df.resample('1s').mean()
            average_val = df.mean(axis=1)
            std_val = df.std(axis=1)
            average_time = df.index.astype('int64')/1e9

            axs[0, count].plot(
                average_val if vertical_time_axis else average_time, 
                average_time if vertical_time_axis else average_val, 
                color=col[i],
                linewidth = 2
            )
            plt_fun = axs[0, count].fill_betweenx if vertical_time_axis else axs[0, count].fill_between
            plt_fun(
                average_time,
                average_val - std_val,
                average_val + std_val,
                color = col[i],
                alpha = 0.3,
                edgecolor = None
            )
        
        for fish_id, data_fish in data_dpf.groupby('fish_id'):
            for cat_value, data_cat in data_fish.groupby(cat):
                if cat_value in keys:
                    axs[0, count].plot(
                        data_cat[val] if vertical_time_axis else  data_cat['time'], 
                        data_cat['time'] if vertical_time_axis else data_cat[val], 
                        color=col[0] if cat_value==keys[0] else col[1] if cat_value==keys[1] else 'k',
                        marker ='o',
                        markevery=[-1],
                        alpha=0.15
                    )
                    if vertical_time_axis:
                        axs[0, count].set_xlabel(xlabel) 
                        axs[0, count].set_ylabel('time (s)')
                    else:
                        axs[0, count].set_xlabel('time (s)') 
                        axs[0, count].set_ylabel(xlabel)
                    summary[cat_value].append(data_cat[val].iloc[end_idx])

        ranksum_plot(
            axs[1, count],
            x = summary[keys[0]], 
            y = summary[keys[1]],
            cat_names=key_names,
            ylabel=xlabel,
            title=f'{dpf} dpf',
            col=col
        )

        count += 1
    
    fig.tight_layout()
    plt.show(block=False)
    plt.savefig(f'{prefix}.svg')
    plt.savefig(f'{prefix}.png')

def plot_dark_vs_bright(data):

    plot_helper(
        data=data, 
        cat='light_condition', 
        val='cum_distance', 
        xlabel='cum. distance (mm)',
        keys = (StimType.BRIGHT, StimType.DARK),
        key_names = ('bright', 'dark'),
        col=COLORS,
        vertical_time_axis=False,
        prefix=os.path.join(RESULT_FOLDER, 'dark_vs_bright')
    )
        
def plot_omr_left_vs_right(data):

    plot_helper(
        data=data, 
        cat='omr_angle', 
        val='angle_unwrapped', 
        xlabel='cum. angle (rad)',
        keys = (90,-90),
        key_names = ('rightwards', 'leftwards'),
        col=COLORS,
        vertical_time_axis=True,
        prefix=os.path.join(RESULT_FOLDER, 'omr_left_vs_right')
    )

def plot_omr_back_vs_front(data):

    plot_helper(
        data=data, 
        cat='omr_angle', 
        val='cum_distance', 
        xlabel='cum. distance (mm)',
        keys = (0,180),
        key_names = ('backwards', 'forwards'),
        col=COLORS,
        vertical_time_axis=False,
        prefix=os.path.join(RESULT_FOLDER, 'omr_backwards_vs_forwards')
    )

def plot_okr_turns(data):

    plot_helper(
        data=data, 
        cat='okr_angle', 
        val='angle_unwrapped', 
        xlabel='cum. angle (rad)',
        keys = (36,-36),
        key_names = ('counterclockwise', 'clockwise'),
        col=COLORS,
        vertical_time_axis=True,
        prefix=os.path.join(RESULT_FOLDER, 'okr_turns')
    )


def plot_phototaxis(data):

    plot_helper(
        data=data, 
        cat='polarity', 
        val='angle_unwrapped', 
        xlabel='cum. angle (rad)',
        keys = (-1,1),
        key_names = ('dark-left', 'dark-right'),
        col=COLORS,
        vertical_time_axis=True,
        prefix=os.path.join(RESULT_FOLDER, 'phototaxis')
    )

def plot_heading_angle(data):
    angle, angle_unwrapped = get_heading_angle(data)
    distance = get_distance(data)

    plt.figure()
    ax1 = plt.subplot(311)
    ax1.plot(
        data['t_local'], 
        angle
    )
    ax2 = plt.subplot(312, sharex=ax1)
    ax2.plot(
        data['t_local'], 
        angle_unwrapped
    )
    ax2.set_ylabel('cum. angle')
    ax3 = plt.subplot(313, sharex=ax1)
    ax3.plot(
        data['t_local'], 
        distance
    )
    ax3.set_ylabel('distance')
    plt.show()


def plot_okr_eyes(data):

    for dpf, data_dpf in data.groupby('dpf'):
        for fish_id, data_fish in data_dpf.groupby('fish_id'):
            fig, ax = plt.subplots(2,  figsize=(15, 5))
            for okr_angle, data_okr in data_fish.groupby('okr_angle'):
                ax_id = 0 if okr_angle == 36 else 1
                ax[ax_id].plot(
                    data_okr['time'], 
                    data_okr['left_eye_angle'], #data_okr['left_eye_angle'].ewm(alpha=0.5).mean(), 
                    color='#158966'
                )
                ax[ax_id].plot(
                    data_okr['time'], 
                    data_okr['right_eye_angle'], 
                    color='#741aaf'
                )
                ax[ax_id].set_xlabel('time (s)')
                ax[ax_id].set_ylabel('eye angle (rad)')
                ax[ax_id].legend(('left eye','right eye'))
            plt.show(block=False)
            plt.savefig(RESULT_FOLDER / f'okr_eyes_{dpf}dpf_fish{fish_id}.svg')
            plt.savefig(RESULT_FOLDER / f'okr_eyes_{dpf}dpf_fish{fish_id}.png')
            plt.close(fig)
     
def plot_loomings(data):

    DISTANCE_THRESHOLD = 0.20

    for dpf, data_dpf in data.groupby('dpf'):

        fig_raster = plt.figure()
        count = -1

        for fish_id, data_fish in data_dpf.groupby('fish_id'):

            fig = plt.figure()
            fig.suptitle(f'{dpf} dpf, fish ID: {fish_id}')
            plt.plot(
                data_fish['time'], 
                data_fish['distance']
            )
            plt.fill_between(
                data_fish['time'],
                data_fish['distance'].max(),
                0,
                where=data_fish['looming_on'],
                alpha=0.2
            )
            plt.xlabel('time (s)')
            plt.ylabel('distance (mm)')
            plt.show(block=False)
            plt.savefig(RESULT_FOLDER / f'looming_distance_{dpf}dpf_fish{fish_id}.svg')
            plt.savefig(RESULT_FOLDER / f'looming_distance_{dpf}dpf_fish{fish_id}.png')
            plt.close(fig)

            looming_boundaries = get_looming_boundaries(data_fish['looming_on'].to_list())
            
            # plot rasterplot of distances
            plt.figure(fig_raster)
            for looming_start, looming_stop in looming_boundaries:
                count += 1
                rel_time = data_fish['time'] - data_fish['time'].iloc[looming_start]
                kept_time = (rel_time > -10) & (rel_time < 20)  

                distance_ewm = data_fish[kept_time]['distance'].ewm(alpha=0.05).mean()
                bouts = 1*(distance_ewm > DISTANCE_THRESHOLD)
                start = np.where(bouts.diff()>0)[0]

                plt.scatter(rel_time[kept_time].iloc[start], count*np.ones((len(start),1)), marker='.', c='black')
 
            fig = plt.figure()
            fig.suptitle(f'{dpf} dpf, fish ID: {fish_id}')
            for start, stop in looming_boundaries:
                trajectory = np.array([
                    [data_fish.iloc[start:stop]['centroid_x'] - data_fish.iloc[start]['centroid_x']],
                    [data_fish.iloc[start:stop]['centroid_y'] - data_fish.iloc[start]['centroid_y']]
                ]).squeeze()
                theta = -looming.iloc[start]['angle']
                rot = np.array([[np.cos(theta), -np.sin(theta)], 
                                [np.sin(theta),  np.cos(theta)]])
                trajectory_egocentric = rot @ trajectory
                
                looming_start_pos = [PIX_PER_MM*15]*2
                plt.plot(
                    trajectory_egocentric[0,:], 
                    trajectory_egocentric[1,:]
                )
                plt.scatter(looming_start_pos[0],looming_start_pos[1], s=20)
                plt.axis('square')
            plt.savefig(RESULT_FOLDER / f'looming_trajectories_{dpf}dpf_fish{fish_id}.svg')
            plt.savefig(RESULT_FOLDER / f'looming_trajectories_{dpf}dpf_fish{fish_id}.png')
            plt.close(fig)

            plt.show(block=False)

        plt.figure(fig_raster)
        plt.title(f'{dpf} dpf')
        plt.axvline(x = 0, color = 'r')
        plt.axvline(x = 2.121, color = 'b')
        plt.axvline(x = 10, color = 'r')
        plt.show(block=False)
        plt.xlabel('time to looming onset (s)')
        plt.ylabel('trial')
        plt.savefig(RESULT_FOLDER / f'looming_raster_{dpf}dpf.svg')
        plt.savefig(RESULT_FOLDER / f'looming_raster_{dpf}dpf.png')

def get_looming_boundaries(bool_vec: Iterable):
    in_region = False
    looming_boundaries = []
    for i in range(len(bool_vec)):
        if bool_vec[i] and not in_region:
            start = i
            in_region = True
        elif not bool_vec[i] and in_region:
            end = i
            looming_boundaries.append((start, end))
            in_region = False
    return looming_boundaries

phototaxis = pd.DataFrame()
omr = pd.DataFrame()
okr = pd.DataFrame()
bright_vs_dark = pd.DataFrame()
looming = pd.DataFrame()

for file in DATAFILES:

    print(file)
    fish_id, dpf, date = parse_filename(file)
    data = pd.read_csv(os.path.join(DATA_FOLDER,file))
    data_filtered = data.groupby('image_index').first()
    data_filtered = data_filtered[1:]
    #data_filtered = remove_data_on_well_edges(data_filtered)
    data_filtered['stim_id'] = data_filtered['stim_id'].astype(int)
    
    bright_vs_dark = pd.concat((
        bright_vs_dark,
        analyse_dark_vs_bright(data_filtered, fish_id, dpf)
    ))

    if file not in EXCLUDE_PHOTOTAXIS:
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


## save 
phototaxis.to_csv(BASE_FOLDER / 'phototaxis.csv')
bright_vs_dark.to_csv(BASE_FOLDER / 'bright_vs_dark.csv')
omr.to_csv(BASE_FOLDER / 'omr.csv')
okr.to_csv(BASE_FOLDER / 'okr.csv')
looming.to_csv(BASE_FOLDER / 'looming.csv')

## load
phototaxis = pd.read_csv(BASE_FOLDER / 'phototaxis.csv')
bright_vs_dark = pd.read_csv(BASE_FOLDER / 'bright_vs_dark.csv')
omr = pd.read_csv(BASE_FOLDER / 'omr.csv')
okr = pd.read_csv(BASE_FOLDER / 'okr.csv')
looming = pd.read_csv(BASE_FOLDER / 'looming.csv')

plot_dark_vs_bright(bright_vs_dark)
plot_phototaxis(phototaxis)
plot_omr_left_vs_right(omr)
plot_omr_back_vs_front(omr)
plot_okr_turns(okr) # TODO: compare the slope of the average (almost linear) to the angular speed of the stimulus (linear regression on the average time series)
plot_loomings(looming) # TODO: make a kind of rasterplot ?
plot_okr_eyes(okr)


