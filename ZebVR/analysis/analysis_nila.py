import matplotlib.patches
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from typing import Tuple, Iterable
from datetime import datetime
import re 
from enum import IntEnum
import seaborn as sns
from scipy.stats import ranksums
import os

PIX_PER_MM = 38.773681409813456
CAM_WIDTH = 2048
CAM_HEIGHT = 2048

matplotlib.rcParams['font.size'] = 12

## NOTE --------------------
# Top projection / Bottom recording: 
#   + angles = fish turns to its left 
#   - angles = fish turns to its right

class StimType(IntEnum):
    DARK = 0
    BRIGHT = 1
    PHOTOTAXIS_CLOSED_LOOP = 2
    OMR_CLOSED_LOOP = 3
    OKR_CLOSED_LOOP = 4
    LINEAR_RADIUS_LOOMING = 5

COLORS = ('#FF6900', '#002BFF')
DATA_FOLDER = 'output/data'

# # experiment computer has locale set to german -_-
import locale
import contextlib
@contextlib.contextmanager
def setlocale(*args, **kw):
    saved = locale.setlocale(locale.LC_ALL)
    yield locale.setlocale(*args, **kw)
    locale.setlocale(locale.LC_ALL, saved)


## Visualization of the results --------------------------------------------------------------------
DATAFILES = [
    '08_09dpf_Di_27_Aug_2024_14h50min47sec.csv', 
    '09_09dpf_Di_27_Aug_2024_16h03min14sec.csv'
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

def analyse_phototaxis(data, fish_id, dpf):
    phototaxis = data[data['stim_id'] == StimType.PHOTOTAXIS_CLOSED_LOOP]

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

def plot_helper(
        data: pd.DataFrame, 
        cat: str, 
        val: str, 
        keys: Iterable, 
        key_names: Iterable, 
        col: Iterable, 
        xlabel:str, 
        vertical_time_axis: bool,
        end_idx: int = -1
    ):

    for dpf, data_dpf in data.groupby('dpf'):
            
        fig = plt.figure()
        fig.suptitle(f'{dpf} dpf')

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

            plt.plot(
                average_val if vertical_time_axis else average_time, 
                average_time if vertical_time_axis else average_val, 
                color=col[i],
                linewidth = 2
            )
            plt_fun =  plt.fill_betweenx if vertical_time_axis else plt.fill_between
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
                    plt.plot(
                        data_cat[val] if vertical_time_axis else  data_cat['time'], 
                        data_cat['time'] if vertical_time_axis else data_cat[val], 
                        color=col[0] if cat_value==keys[0] else col[1] if cat_value==keys[1] else 'k',
                        marker ='o',
                        markevery=[-1],
                        alpha=0.15
                    )
                    if vertical_time_axis:
                        plt.xlabel(xlabel) 
                        plt.ylabel('time (s)')
                    else:
                        plt.xlabel('time (s)') 
                        plt.ylabel(xlabel)
                    summary[cat_value].append(data_cat[val].iloc[end_idx])

        plt.show(block=False)

        ranksum_plot(
            x = summary[keys[0]], 
            y = summary[keys[1]],
            cat_names=key_names,
            ylabel=xlabel,
            title=f'{dpf} dpf',
            col=col
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
        vertical_time_axis=True
    )

phototaxis = pd.DataFrame()

for file in DATAFILES:

    print(file)
    fish_id, dpf, date = parse_filename(file)
    data = pd.read_csv(os.path.join(DATA_FOLDER,file))
    data_filtered = data.groupby('image_index').first()
    data_filtered = data_filtered[1:]
    data_filtered['stim_id'] = data_filtered['stim_id'].astype(int)
    

    phototaxis = pd.concat((
        phototaxis, 
        analyse_phototaxis(data_filtered, fish_id, dpf)
    ))

## save 
phototaxis.to_csv('phototaxis.csv')

## load
phototaxis = pd.read_csv('phototaxis.csv')

plot_phototaxis(phototaxis)


