from pathlib import Path
from multiprocessing import Pool
from functools import partial

from .load import (
    Directories, 
    BehaviorFiles,
    find_files, 
    load_data
)
from .process import (
    compute_tracking_metrics, 
    compute_trajectories,
    superimpose_video_trials
)
from .plot import (
    plot_tracking_metrics, 
    plot_trajectories
)

# TODO eye tracking OKR
# TODO eye tracking + tail tracking and classification J-turn PREY_CAPTURE
# TODO bout segmentation and distribution of heading change per bout
# TODO bout classification for every behavior + ethogram? 
# TODO overlay video trials
# TODO average trial-average over fish
# TODO plot trajectories / heatmap position for each stimulus 
# TODO filter bouts on edges?
# TODO separate analysis and plotting. Use multiprocessing for analysis here

def extract_videos(behavior_file: BehaviorFiles, directories: Directories):
    behavior_data = load_data(behavior_file)
    superimpose_video_trials(directories, behavior_data, behavior_file, 30)

def run(behavior_file: BehaviorFiles):
    behavior_data = load_data(behavior_file)
    metrics = compute_tracking_metrics(behavior_data)
    #trajectories = compute_trajectories(behavior_data)

    for identity, data in metrics.items():
        plot_tracking_metrics(data)

    # for identity, data in trajectories.items():
    #     plot_trajectories(data)
    
if __name__ == '__main__':

    base_dir = Path('/media/martin/MARTIN_8TB_0/Work/Baier/DATA/Behavioral_screen/output')
    #base_dir = Path('/media/martin/DATA/Behavioral_screen/output')
    directories = Directories(base_dir)
    behavior_files = find_files(directories)

    _extract_videos = partial(extract_videos, directories = directories)
    # NOTE all behavior data loaded in RAM can be heavy
    with Pool(processes=16) as pool:
        pool.map(_extract_videos, behavior_files)

    for behavior_file in behavior_files:
        run(behavior_file)