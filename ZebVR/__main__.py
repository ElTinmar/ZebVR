import time

from multiprocessing import set_start_method, Process
import os
os.environ["OMP_NUM_THREADS"] = "1" # this may not be necessary when setting affinity
from PyQt5.QtWidgets import QApplication
import pickle
import sys
import pprint
from pathlib import Path

def set_realtime_priority(priority):
    
    try:
        # Get the current process ID
        pid = os.getpid()
        
        # Set real-time scheduling policy and priority
        os.sched_setscheduler(pid, os.SCHED_RR, os.sched_param(sched_priority=priority))
        print(f"Real-time priority set to {priority}.")

    except PermissionError:
        print("Permission denied. Run as root or grant CAP_SYS_NICE to the Python executable.")

    except Exception as e:
        print(f"Failed to set real-time priority: {e}")

def run_vr_file(vr_file, *args) -> None:

    from .dags import open_loop, closed_loop, video_recording, tracking
    from .utils import append_timestamp_to_filename

    with open(vr_file, 'rb') as fp:
        settings = pickle.load(fp)

    settings['main']['record'] = True

    pprint.pprint(settings)
    prefix = Path(settings['settings']['prefix'])
    filename = prefix.with_suffix('.metadata')
    filename = append_timestamp_to_filename(filename)       
    with open(filename,'w') as fp:
        pprint.pprint(settings, fp) 

    if settings['main']['open_loop']:
        dag, worker_logger, queue_logger = open_loop(settings)
    elif settings['main']['close_loop']:
        dag, worker_logger, queue_logger = closed_loop(settings)
    elif settings['main']['video_recording']:
        dag, worker_logger, queue_logger = video_recording(settings)
    elif settings['main']['tracking']:
        dag, worker_logger, queue_logger = tracking(settings)

    p_worker_logger = Process(target=worker_logger.run)
    p_queue_logger = Process(target=queue_logger.run)
    p_worker_logger.start()
    p_queue_logger.start()
    dag.start()

    try:
        time.sleep(settings['main']['recording_duration'])
    except KeyboardInterrupt:
        print('stopping')
        pass

    dag.stop()
    worker_logger.stop()
    queue_logger.stop()
    p_worker_logger.join()
    p_queue_logger.join()

def main():

    # set_realtime_priority(99)  # optional
    set_start_method('spawn')

    if len(sys.argv) > 1:
        # CLI mode
        vr_file = sys.argv[1]
        run_vr_file(vr_file, *sys.argv[2:])

    else:
        # GUI mode

        from .gui import MainGui

        app = QApplication(sys.argv)
        main_window = MainGui()
        main_window.show()
        app.exec_()

if __name__ == "__main__":
    main()
