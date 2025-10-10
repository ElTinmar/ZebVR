from pathlib import Path

from .load import (
    Directories, 
    BehaviorFiles,
    find_files, 
    load_data
)
from .process import (
    compute_tracking_metrics, 
    compute_trajectories
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

def run(behavior_files: BehaviorFiles):

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

    for behavior_file in behavior_files:
        run(behavior_file)