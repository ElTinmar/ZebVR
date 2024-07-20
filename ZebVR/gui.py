from multiprocessing import Process
from multiprocessing_logger import Logger
from dagline import ProcessingDAG
import subprocess
import time
from typing import Dict
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QPushButton
from qt_widgets import LabeledEditLine, LabeledSpinBox

from config import (
    N_BACKGROUND_WORKERS, 
    N_TRACKER_WORKERS,
    RECORD_VIDEO,
)

#NOTE this is tightly coupled with main.py through the keys present in the Dicts
class MainGui(QWidget):
    
    def __init__(self, workers: Dict, queues: Dict, worker_logger: Logger, queue_logger: Logger, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.dag = None
        self.workers = workers
        self.queues = queues
        self.worker_logger = worker_logger
        self.queue_logger = queue_logger
        self.setWindowTitle('Main controls')
        self.create_components()
        self.layout_components()

    def create_dag(self):

        # clear workers and queues

        for key, worker in self.workers.items():
            worker.reset()

        for key, queue in self.queues.items():
            queue.clear()

        self.dag = ProcessingDAG()

        # data
        for i in range(N_BACKGROUND_WORKERS):   
            self.dag.connect_data(
                sender=self.workers['camera'], 
                receiver=self.workers[f'background_{i}'], 
                queue=self.queues['camera_to_background'], 
                name='background_subtraction'
            )
        
        # NOTE: the order in which you declare connections matter: background_subtraction will
        # be served before image_saver
        if RECORD_VIDEO:
            self.dag.connect_data(
                sender=self.workers['camera'], 
                receiver=self.workers['video_recorder'], 
                queue=self.queues['camera_to_video_recorder'], 
                name='image_saver'
            )

        for i in range(N_BACKGROUND_WORKERS):
            for j in range(N_TRACKER_WORKERS):
                self.dag.connect_data(
                    sender=self.workers[f'background_{i}'], 
                    receiver=self.workers[f'tracker_{j}'], 
                    queue=self.queues['background_to_tracker'], 
                    name='background_subtracted'
                )

        self.dag.connect_data(
            sender=self.workers['overlay'], 
            receiver=self.workers['display'], 
            queue=self.queues['overlay_to_display'], 
            name='disp'
        )

        for i in range(N_TRACKER_WORKERS):
            self.dag.connect_data(
                sender=self.workers[f'tracker_{i}'], 
                receiver=self.workers['overlay'], 
                queue=self.queues['tracker_to_overlay'], 
                name='overlay'
            )

        for i in range(N_TRACKER_WORKERS):
            self.dag.connect_data(
                sender=self.workers[f'tracker_{i}'], 
                receiver=self.workers['visual_stim'], 
                queue=self.queues['tracker_to_stim'], 
                name='stimulus'
            )

        # metadata
        self.dag.connect_metadata(
            sender=self.workers['camera_gui'], 
            receiver=self.workers['camera'], 
            queue=self.queues['camera_control_to_camera'], 
            name='camera_control'
        )
        
        self.dag.connect_metadata(
            sender=self.workers['camera'], 
            receiver=self.workers['camera_gui'], 
            queue=self.queues['camera_to_camera_control'], 
            name='camera_info'
        )

        self.dag.connect_metadata(
            sender=self.workers['visual_stim_control'], 
            receiver=self.workers['visual_stim'], 
            queue=self.queues['visual_stim_control'], 
            name='visual_stim_control'
        )
        
        for i in range(N_TRACKER_WORKERS):
            self.dag.connect_metadata(
                sender=self.workers['tracker_gui'], 
                receiver=self.workers[f'tracker_{i}'], 
                queue=self.queues[f'tracker_control_to_tracker_{i}'], 
                name=f'tracker_control_{i}'
            )

    def create_components(self):
        
        # calibration
        self.registration_button = QPushButton()
        self.registration_button.setText('registration')
        self.registration_button.clicked.connect(self.registration)

        self.check_registration_button = QPushButton()
        self.check_registration_button.setText('check registration')
        self.check_registration_button.clicked.connect(self.check_registration)

        self.pixel_size_button = QPushButton()
        self.pixel_size_button.setText('get pix/mm')
        self.pixel_size_button.clicked.connect(self.get_pix_per_mm)

        self.check_pixel_size_button = QPushButton()
        self.check_pixel_size_button.setText('check pix/mm')
        self.check_pixel_size_button.clicked.connect(self.check_pix_per_mm)

        self.label_method = QLabel()
        self.label_method.setText('Background type:')
        self.background_method = QComboBox()
        self.background_method.addItem('static')
        self.background_method.addItem('inpaint')

        self.background_button = QPushButton()
        self.background_button.setText('background')
        self.background_button.clicked.connect(self.background)

        # experiment
        self.fish_id = LabeledSpinBox()
        self.fish_id.setText('Fish ID:')
        self.fish_id.setValue(0)
        self.fish_id.valueChanged.connect(self.experiment_data)

        self.dpf = LabeledSpinBox()
        self.dpf.setText('Fish age (dpf):')
        self.dpf.setValue(7)
        self.dpf.valueChanged.connect(self.experiment_data)

        self.duration = LabeledSpinBox()
        self.duration.setText('rec. duration (s)')
        self.duration.setValue(60)
        self.duration.valueChanged.connect(self.experiment_data)

        self.filename = LabeledEditLine()
        self.filename.setLabel('result file:')
        
        self.start_button = QPushButton()
        self.start_button.setText('start')
        self.start_button.clicked.connect(self.start)

        self.stop_button = QPushButton()
        self.stop_button.setText('stop')
        self.stop_button.clicked.connect(self.stop)

        self.record_button = QPushButton()
        self.record_button.setText('record')
        self.record_button.clicked.connect(self.record)

    def layout_components(self):
        
        controls = QHBoxLayout()
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)
        controls.addWidget(self.record_button)

        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(self.registration_button)
        layout.addWidget(self.check_registration_button)
        layout.addWidget(self.pixel_size_button)
        layout.addWidget(self.check_pixel_size_button)
        layout.addWidget(self.label_method)
        layout.addWidget(self.background_method)
        layout.addWidget(self.background_button)
        layout.addWidget(self.fish_id)
        layout.addWidget(self.dpf)
        layout.addWidget(self.duration)
        layout.addWidget(self.filename)
        layout.addLayout(controls)
        layout.addStretch()

    def experiment_data(self):
        pass

    def registration(self):
        subprocess.Popen(['python', 'ZebVR/calibration/registration.py'])

    def check_registration(self):
        subprocess.Popen(['python', 'ZebVR/calibration/check_registration.py'])

    def background(self):
        if self.background_method.currentText() == 'inpaint':
            subprocess.Popen(['python', 'ZebVR/background/inpaint_background.py'])
        elif self.background_method.currentText() == 'static':
            subprocess.Popen(['python', 'ZebVR/background/static_background.py'])

    def get_pix_per_mm(self):
        subprocess.Popen(['python', 'ZebVR/calibration/pix_per_mm.py'])

    def check_pix_per_mm(self):
        subprocess.Popen(['python', 'ZebVR/calibration/check_pix_per_mm.py'])
    
    def start(self):
        self.create_dag()
        self.p_worker_logger = Process(target=self.worker_logger.run)
        self.p_queue_logger = Process(target=self.queue_logger.run)
        self.p_worker_logger.start()
        self.p_queue_logger.start()
        print('Starting DAG')
        self.dag.start()

    def stop(self):
        if self.dag is not None:
            self.dag.stop()
            print('cam to background', self.queues['camera_to_background'].get_average_freq(), self.queues['camera_to_background'].queue.num_lost_item.value)
            if RECORD_VIDEO:
                print('cam to image saver', self.queues['camera_to_video_recorder'].get_average_freq(), self.queues['camera_to_video_recorder'].queue.num_lost_item.value)
            print('background to trackers', self.queues['background_to_tracker'].get_average_freq(), self.queues['background_to_tracker'].queue.num_lost_item.value)
            print('trackers to visual stim', self.queues['tracker_to_stim'].get_average_freq(), self.queues['tracker_to_stim'].queue.num_lost_item.value)
            print('trackers to overlay', self.queues['tracker_to_overlay'].get_average_freq(), self.queues['tracker_to_overlay'].queue.num_lost_item.value)
            print('overlay to display', self.queues['overlay_to_display'].get_average_freq(), self.queues['overlay_to_display'].queue.num_lost_item.value)
            self.worker_logger.stop()
            self.queue_logger.stop()
            self.p_worker_logger.join()
            self.p_queue_logger.join()
            print('DAG stopped')

    def record(self):
        self.start()
        time.sleep(self.duration.value())
        self.stop()