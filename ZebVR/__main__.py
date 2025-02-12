from multiprocessing import set_start_method
import os
os.environ["OMP_NUM_THREADS"] = "1" # this may not be necessary when setting affinity
from PyQt5.QtWidgets import QApplication
from .gui import MainGui

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

if __name__ == "__main__":

    #set_realtime_priority(99)
    set_start_method('spawn')

    app = QApplication([])
    main = MainGui()
    main.show()
    app.exec_()
