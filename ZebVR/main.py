from multiprocessing import set_start_method
import os
os.environ["OMP_NUM_THREADS"] = "1"
from PyQt5.QtWidgets import QApplication
from ZebVR.gui import MainGui

if __name__ == "__main__":

    set_start_method('spawn')

    app = QApplication([])
    main = MainGui()
    main.show()
    app.exec_()



    workers = {
        'camera': cam,
        'video_recorder': image_saver,
        'visual_stim': stim_worker,
        'tracking_display': trck_disp,
        'camera_gui': cam_control,
        'visual_stim_control': stim_control,
        'protocol': protocol,
        'tracker_gui': tracker_control
    }
    for i in range(N_TRACKER_WORKERS):
        workers[f'tracker_{i}'] = trck[i]
    for i in range(N_BACKGROUND_WORKERS):
        workers[f'background_{i}'] = bckg[i]
        
    queues = {
        'camera_to_background': q_cam,
        'camera_to_video_recorder': q_save_image,
        'background_to_tracker': q_back,
        'tracker_to_stim': q_tracking,
        'tracker_to_tracking_display': q_overlay,
        'camera_control_to_camera': QueueMP(),
        'camera_to_camera_control': QueueMP(),
        'visual_stim_control': QueueMP()
    }
    for i in range(N_TRACKER_WORKERS):
        queues[f'tracker_control_to_tracker_{i}'] = QueueMP()


