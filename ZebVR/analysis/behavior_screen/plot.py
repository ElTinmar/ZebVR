from ZebVR.protocol import Stim
from typing import List, Dict, Callable, Sequence
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from .process import common_time, interpolate_ts

COLORS = ("#F1500A", "#0A6EF1")

def plot_helper(
        ax: Axes,
        metrics: Dict,
        trial_duration_s: float,
        fps: float,
        group_names: List, 
        value_func: Callable, 
        group_func: Callable,
        color_func: Callable = lambda group_idx: 'k',
    ):

    num_trials = len(metrics['relative_time'])
    target_time = common_time(trial_duration_s, fps)
    trials = [np.zeros((len(target_time), 0)), np.zeros((len(target_time), 0))] 

    for trial_idx in range(num_trials):
        group_idx = group_func(metrics, trial_idx)
        value = interpolate_ts(
            target_time, 
            metrics['relative_time'][trial_idx],
            value_func(metrics, trial_idx)
        )
        ax.plot(
            target_time, 
            value,
            color = color_func(group_idx),
            alpha=0.2
        )
        trials[group_idx] = np.column_stack((trials[group_idx], value)) 

    for group_idx, name in enumerate(group_names):
        avg = np.mean(trials[group_idx], axis=1)
        sem = np.std(trials[group_idx], axis=1, ddof=1)
        ax.plot(target_time, avg, color = color_func(group_idx))
        ax.fill_between(
            target_time, 
            avg - sem, 
            avg + sem, 
            color = color_func(group_idx), 
            alpha = 0.2, 
            edgecolor = 'none'
        )

    ax.legend(group_names)

def plot_dark(metrics: Dict, ax: Sequence[Axes]):
    plot_helper(
        ax[0],
        metrics, 
        trial_duration_s = 30,
        fps = 100,
        group_names = ['dark'],
        value_func = lambda metrics, trial_idx: np.cumsum(metrics['distance_traveled'][trial_idx]),
        group_func = lambda metrics, trial_idx: 0,
        color_func = lambda group_idx: 'k'
    )
    ax[0].set_title('dark')
    plot_helper(
        ax[1],
        metrics, 
        trial_duration_s = 30,
        fps = 100,
        group_names = ['dark'],
        value_func = lambda metrics, trial_idx: metrics['theta_unwrapped'][trial_idx],
        group_func = lambda metrics, trial_idx: 0, 
        color_func = lambda group_idx: 'k'
    )
    ax[1].set_title('dark')

def plot_bright(metrics: Dict, ax: Axes):
    plot_helper(
        ax,
        metrics, 
        trial_duration_s = 30,
        fps = 100,
        group_names = ['bright'],
        value_func = lambda metrics, trial_idx: np.cumsum(metrics['distance_traveled'][trial_idx]),
        group_func = lambda metrics, trial_idx: 0,
        color_func = lambda group_idx: 'k'
    )
    ax.set_title('bright')

def plot_phototaxis(metrics: Dict, ax: Axes):
    plot_helper(
        ax,
        metrics, 
        trial_duration_s = 30,
        fps = 100,
        group_names = ['-1', '1'],
        value_func = lambda metrics, trial_idx: metrics['theta_unwrapped'][trial_idx],
        group_func = lambda metrics, trial_idx: 0 if metrics['parameters'][trial_idx]['phototaxis_polarity'] == -1 else 1, # TODO check
        color_func = lambda group_idx: COLORS[group_idx]
    )
    ax.set_title('phototaxis')

def plot_omr(metrics: Dict, ax: Axes):
    plot_helper(
        ax,
        metrics, 
        trial_duration_s = 30,
        fps = 100,
        group_names = ['-90', '90'],
        value_func = lambda metrics, trial_idx: metrics['theta_unwrapped'][trial_idx],
        group_func = lambda metrics, trial_idx: 0 if metrics['parameters'][trial_idx]['omr_angle_deg'] == -90 else 1, 
        color_func = lambda group_idx: COLORS[group_idx]
    )
    ax.set_title('omr')

def plot_okr(metrics: Dict, ax: Axes):
    plot_helper(
        ax,
        metrics, 
        trial_duration_s = 30,
        fps = 100,
        group_names = ['-36', '36'],
        value_func = lambda metrics, trial_idx: metrics['theta_unwrapped'][trial_idx],
        group_func = lambda metrics, trial_idx: 0 if metrics['parameters'][trial_idx]['okr_speed_deg_per_sec'] == -36 else 1, 
        color_func = lambda group_idx: COLORS[group_idx]
    )
    ax.set_title('okr')

def plot_loomings(metrics: Dict, ax: Sequence[Axes]):
    plot_helper(
        ax[0],
        metrics, 
        trial_duration_s = 10,
        fps = 100,
        group_names = ['-2', '2'],
        value_func = lambda metrics, trial_idx: metrics['theta_unwrapped'][trial_idx],
        group_func = lambda metrics, trial_idx: 0 if metrics['parameters'][trial_idx]['looming_center_mm'][0] == -2 else 1, 
        color_func = lambda group_idx: COLORS[group_idx]
    )
    ax[0].set_title('loomings')
    plot_helper(
        ax[1],
        metrics, 
        trial_duration_s = 10,
        fps = 100,
        group_names = [''],
        value_func = lambda metrics, trial_idx: metrics['speed'][trial_idx],
        group_func = lambda metrics, trial_idx: 0, 
        color_func = lambda group_idx: 'k'
    )
    ax[1].set_title('loomings')

def plot_prey_capture(metrics: Dict, ax: Axes):
    plot_helper(
        ax,
        metrics, 
        trial_duration_s = 30,
        fps = 100,
        group_names = ['-20', '20'],
        value_func = lambda metrics, trial_idx: metrics['theta_unwrapped'][trial_idx],
        group_func = lambda metrics, trial_idx: 0 if metrics['parameters'][trial_idx]['prey_arc_start_deg'] == -20 else 1, 
        color_func = lambda group_idx: COLORS[group_idx]
    )
    ax.set_title('prey capture')

def plot_tracking_metrics(metrics: Dict):

    fig, axes = plt.subplots(3,3, figsize=(12,12))
    plot_dark(metrics[Stim.DARK], axes[0][0:2])
    plot_bright(metrics[Stim.BRIGHT], axes[0,2])
    plot_phototaxis(metrics[Stim.PHOTOTAXIS], axes[1,0])
    plot_omr(metrics[Stim.OMR], axes[1,1])
    plot_okr(metrics[Stim.OKR], axes[1,2])
    plot_prey_capture(metrics[Stim.PREY_CAPTURE], axes[2,0])
    plot_loomings(metrics[Stim.LOOMING], axes[2][1:3])
    plt.tight_layout()
    plt.show(block=False)

def plot_trajectories_helper(trajectories: Dict, ax:Axes, title):
    num_trials = len(trajectories['x'])
    for trial_idx in range(num_trials):
        ax.plot(
            trajectories['x'][trial_idx], 
            trajectories['y'][trial_idx], 
            color = 'k', 
            alpha = 0.4
        )
    ax.set_title(title)
    
def plot_trajectories(trajectories: Dict):

    fig, axes = plt.subplots(3,3, figsize=(12,12))
    plot_trajectories_helper(trajectories[Stim.DARK], axes[0,0], title='dark')
    plot_trajectories_helper(trajectories[Stim.BRIGHT], axes[0,1], title='bright')
    plot_trajectories_helper(trajectories[Stim.PHOTOTAXIS], axes[0,2], title='phototaxis')
    plot_trajectories_helper(trajectories[Stim.OMR], axes[1,0], title='OMR')
    plot_trajectories_helper(trajectories[Stim.OKR], axes[1,1], title='OKR')
    plot_trajectories_helper(trajectories[Stim.PREY_CAPTURE], axes[1,2], title='prey capture')
    plot_trajectories_helper(trajectories[Stim.LOOMING], axes[2,0], title='looming')
    plt.tight_layout()
    plt.show(block=False)