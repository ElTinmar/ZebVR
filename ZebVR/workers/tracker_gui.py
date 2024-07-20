from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from qt_widgets import LabeledDoubleSpinBox

class TrackerGui(WorkerNode):

    def __init__(
            self,
            animal_tracking_param: Dict,
            body_tracking_param: Dict,
            eyes_tracking_param: Dict,
            tail_tracking_param: Dict,
            n_tracker_workers: int,
            *args,
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.animal_tracking_param = animal_tracking_param 
        self.body_tracking_param = body_tracking_param 
        self.eyes_tracking_param = eyes_tracking_param 
        self.tail_tracking_param = tail_tracking_param 
        self.n_tracker_workers = n_tracker_workers 

    def initialize(self) -> None:
        super().initialize()
        
        self.updated = False
        self.app = QApplication([])
        self.window = QWidget()
        self.declare_components()
        self.layout_components()
        self.window.setWindowTitle('Tracking controls')
        self.window.show()

    def declare_components(self):
        self.animal_pix_per_mm = LabeledDoubleSpinBox()
        self.animal_pix_per_mm.setText('pix/mm')
        self.animal_pix_per_mm.setRange(0,200)
        self.animal_pix_per_mm.setValue(self.animal_tracking_param['pix_per_mm'])
        self.animal_pix_per_mm.valueChanged.connect(self.on_change)

        self.animal_target_pix_per_mm = LabeledDoubleSpinBox()
        self.animal_target_pix_per_mm.setText('target pix/mm')
        self.animal_target_pix_per_mm.setRange(0,200)
        self.animal_target_pix_per_mm.setValue(self.animal_tracking_param['target_pix_per_mm'])
        self.animal_target_pix_per_mm.valueChanged.connect(self.on_change)

        self.animal_intensity = LabeledDoubleSpinBox()
        self.animal_intensity.setText('intensity')
        self.animal_intensity.setRange(0,1)
        self.animal_intensity.setValue(self.animal_tracking_param['animal_intensity'])
        self.animal_intensity.valueChanged.connect(self.on_change)

        self.animal_brightness = LabeledDoubleSpinBox()
        self.animal_brightness.setText('brightness')
        self.animal_brightness.setRange(-1,1)
        self.animal_brightness.setValue(self.animal_tracking_param['animal_brightness'])
        self.animal_brightness.valueChanged.connect(self.on_change)

        self.animal_gamma = LabeledDoubleSpinBox()
        self.animal_gamma.setText('gamma')
        self.animal_gamma.setRange(-10,10)
        self.animal_gamma.setValue(self.animal_tracking_param['animal_gamma'])
        self.animal_gamma.valueChanged.connect(self.on_change)
        
        self.animal_contrast = LabeledDoubleSpinBox()
        self.animal_contrast.setText('contrast')
        self.animal_contrast.setRange(-10,10)
        self.animal_contrast.setValue(self.animal_tracking_param['animal_contrast'])
        self.animal_contrast.valueChanged.connect(self.on_change)

        self.animal_min_size_mm = LabeledDoubleSpinBox()
        self.animal_min_size_mm.setText('min area (mm2)')
        self.animal_min_size_mm.setRange(0,100_000)
        self.animal_min_size_mm.setValue(self.animal_tracking_param['min_animal_size_mm'])
        self.animal_min_size_mm.valueChanged.connect(self.on_change)

        self.animal_max_size_mm = LabeledDoubleSpinBox()
        self.animal_max_size_mm.setText('max area (mm2)')
        self.animal_max_size_mm.setRange(0,100_000)
        self.animal_max_size_mm.setValue(self.animal_tracking_param['max_animal_size_mm'])
        self.animal_max_size_mm.valueChanged.connect(self.on_change)

        self.animal_min_length_mm = LabeledDoubleSpinBox()
        self.animal_min_length_mm.setText('min öength (mm)')
        self.animal_min_length_mm.setRange(0,100_000)
        self.animal_min_length_mm.setValue(self.animal_tracking_param['min_animal_length_mm'])
        self.animal_min_length_mm.valueChanged.connect(self.on_change)

        self.animal_max_length_mm = LabeledDoubleSpinBox()
        self.animal_max_length_mm.setText('max length (mm)')
        self.animal_max_length_mm.setRange(0,100_000)
        self.animal_max_length_mm.setValue(self.animal_tracking_param['max_animal_length_mm'])
        self.animal_max_length_mm.valueChanged.connect(self.on_change)

        self.animal_min_width_mm = LabeledDoubleSpinBox()
        self.animal_min_width_mm.setText('min width (mm)')
        self.animal_min_width_mm.setRange(0,100_000)
        self.animal_min_width_mm.setValue(self.animal_tracking_param['min_animal_width_mm'])
        self.animal_min_width_mm.valueChanged.connect(self.on_change)

        self.animal_max_width_mm = LabeledDoubleSpinBox()
        self.animal_max_width_mm.setText('max width (mm)')
        self.animal_max_width_mm.setRange(0,100_000)
        self.animal_max_width_mm.setValue(self.animal_tracking_param['max_animal_width_mm'])
        self.animal_max_width_mm.valueChanged.connect(self.on_change)

        self.animal_blur_sz_mm = LabeledDoubleSpinBox()
        self.animal_blur_sz_mm.setText('blur size (mm)')
        self.animal_blur_sz_mm.setRange(0,1000)
        self.animal_blur_sz_mm.setSingleStep(1/self.animal_tracking_param['target_pix_per_mm'])
        self.animal_blur_sz_mm.setValue(self.animal_tracking_param['blur_sz_mm'])
        self.animal_blur_sz_mm.valueChanged.connect(self.on_change)
        
        self.animal_median_filter_sz_mm = LabeledDoubleSpinBox()
        self.animal_median_filter_sz_mm.setText('medfilt size (mm)')
        self.animal_median_filter_sz_mm.setRange(0,1000)
        self.animal_median_filter_sz_mm.setSingleStep(1/self.animal_tracking_param['target_pix_per_mm'])
        self.animal_median_filter_sz_mm.setValue(self.animal_tracking_param['median_filter_sz_mm'])
        self.animal_median_filter_sz_mm.valueChanged.connect(self.on_change)

        self.body_pix_per_mm = LabeledDoubleSpinBox()
        self.body_pix_per_mm.setText('pix/mm')
        self.body_pix_per_mm.setRange(0,200)
        self.body_pix_per_mm.setValue(self.body_tracking_param['pix_per_mm'])
        self.body_pix_per_mm.valueChanged.connect(self.on_change)
        
        self.body_target_pix_per_mm = LabeledDoubleSpinBox()
        self.body_target_pix_per_mm.setText('target pix/mm')
        self.body_target_pix_per_mm.setRange(0,200)
        self.body_target_pix_per_mm.setValue(self.body_tracking_param['target_pix_per_mm'])
        self.body_target_pix_per_mm.valueChanged.connect(self.on_change)
        
        self.body_intensity = LabeledDoubleSpinBox()
        self.body_intensity.setText('intensity')
        self.body_intensity.setRange(0,1)
        self.body_intensity.setValue(self.body_tracking_param['body_intensity'])
        self.body_intensity.valueChanged.connect(self.on_change)

        self.body_brightness = LabeledDoubleSpinBox()
        self.body_brightness.setText('brightness')
        self.body_brightness.setRange(-1,1)
        self.body_brightness.setValue(self.body_tracking_param['body_brightness'])
        self.body_brightness.valueChanged.connect(self.on_change)

        self.body_gamma = LabeledDoubleSpinBox()
        self.body_gamma.setText('gamma')
        self.body_gamma.setRange(-10,10)
        self.body_gamma.setValue(self.body_tracking_param['body_gamma'])
        self.body_gamma.valueChanged.connect(self.on_change)

        self.body_contrast = LabeledDoubleSpinBox()
        self.body_contrast.setText('contrast')
        self.body_contrast.setRange(-10,10)
        self.body_contrast.setValue(self.body_tracking_param['body_contrast'])
        self.body_contrast.valueChanged.connect(self.on_change)

        self.body_min_size_mm = LabeledDoubleSpinBox()
        self.body_min_size_mm.setText('min area (mm2)')
        self.body_min_size_mm.setRange(0,100_000)
        self.body_min_size_mm.setValue(self.body_tracking_param['min_body_size_mm'])
        self.body_min_size_mm.valueChanged.connect(self.on_change)

        self.body_max_size_mm = LabeledDoubleSpinBox()
        self.body_max_size_mm.setText('max area (mm2)')
        self.body_max_size_mm.setRange(0,100_000)
        self.body_max_size_mm.setValue(self.body_tracking_param['max_body_size_mm'])
        self.body_max_size_mm.valueChanged.connect(self.on_change)

        self.body_min_length_mm = LabeledDoubleSpinBox()
        self.body_min_length_mm.setText('min length (mm)')
        self.body_min_length_mm.setRange(0,100_000)
        self.body_min_length_mm.setValue(self.body_tracking_param['min_body_length_mm'])
        self.body_min_length_mm.valueChanged.connect(self.on_change)

        self.body_max_length_mm = LabeledDoubleSpinBox()
        self.body_max_length_mm.setText('max length (mm)')
        self.body_max_length_mm.setRange(0,100_000)
        self.body_max_length_mm.setValue(self.body_tracking_param['max_body_length_mm'])
        self.body_max_length_mm.valueChanged.connect(self.on_change)

        self.body_min_width_mm = LabeledDoubleSpinBox()
        self.body_min_width_mm.setText('min width (mm)')
        self.body_min_width_mm.setRange(0,100_000)
        self.body_min_width_mm.setValue(self.body_tracking_param['min_body_width_mm'])
        self.body_min_width_mm.valueChanged.connect(self.on_change)

        self.body_max_width_mm = LabeledDoubleSpinBox()
        self.body_max_width_mm.setText('max width (mm)')
        self.body_max_width_mm.setRange(0,100_000)
        self.body_max_width_mm.setValue(self.body_tracking_param['max_body_width_mm'])
        self.body_max_width_mm.valueChanged.connect(self.on_change)

        self.body_blur_sz_mm = LabeledDoubleSpinBox()
        self.body_blur_sz_mm.setText('blur size (mm)')
        self.body_blur_sz_mm.setRange(0,1000)
        self.body_blur_sz_mm.setSingleStep(1/self.body_tracking_param['target_pix_per_mm'])
        self.body_blur_sz_mm.setValue(self.body_tracking_param['blur_sz_mm'])
        self.body_blur_sz_mm.valueChanged.connect(self.on_change)

        self.body_median_filter_sz_mm = LabeledDoubleSpinBox()
        self.body_median_filter_sz_mm.setText('medfilt size (mm)')
        self.body_median_filter_sz_mm.setRange(0,1000)
        self.body_median_filter_sz_mm.setSingleStep(1/self.body_tracking_param['target_pix_per_mm'])
        self.body_median_filter_sz_mm.setValue(self.body_tracking_param['median_filter_sz_mm'])
        self.body_median_filter_sz_mm.valueChanged.connect(self.on_change)

        self.eyes_pix_per_mm = LabeledDoubleSpinBox()
        self.eyes_pix_per_mm.setText('pix/mm')
        self.eyes_pix_per_mm.setRange(0,200)
        self.eyes_pix_per_mm.setValue(self.eyes_tracking_param['pix_per_mm'])
        self.eyes_pix_per_mm.valueChanged.connect(self.on_change)
        
        self.eyes_target_pix_per_mm = LabeledDoubleSpinBox()
        self.eyes_target_pix_per_mm.setText('target pix/mm')
        self.eyes_target_pix_per_mm.setRange(0,200)
        self.eyes_target_pix_per_mm.setValue(self.eyes_tracking_param['target_pix_per_mm'])
        self.eyes_target_pix_per_mm.valueChanged.connect(self.on_change)
        
        self.eyes_intensity_lo = LabeledDoubleSpinBox()
        self.eyes_intensity_lo.setText('thresh low')
        self.eyes_intensity_lo.setRange(0,1)
        self.eyes_intensity_lo.setValue(self.eyes_tracking_param['eye_thresh_lo'])
        self.eyes_intensity_lo.valueChanged.connect(self.on_change)

        self.eyes_intensity_hi = LabeledDoubleSpinBox()
        self.eyes_intensity_hi.setText('thresh high')
        self.eyes_intensity_hi.setRange(0,1)
        self.eyes_intensity_hi.setValue(self.eyes_tracking_param['eye_thresh_hi'])
        self.eyes_intensity_hi.valueChanged.connect(self.on_change)

        self.eyes_thresh_resolution = LabeledDoubleSpinBox()
        self.eyes_thresh_resolution.setText('thresh steps')
        self.eyes_thresh_resolution.setRange(0,100)
        self.eyes_thresh_resolution.setValue(self.eyes_tracking_param['eye_dyntresh_res'])
        self.eyes_thresh_resolution.valueChanged.connect(self.on_change)

        self.eyes_brightness = LabeledDoubleSpinBox()
        self.eyes_brightness.setText('brightness')
        self.eyes_brightness.setRange(-1,1)
        self.eyes_brightness.setValue(self.eyes_tracking_param['eye_brightness'])
        self.eyes_brightness.valueChanged.connect(self.on_change)

        self.eyes_gamma = LabeledDoubleSpinBox()
        self.eyes_gamma.setText('gamma')
        self.eyes_gamma.setRange(-10,10)
        self.eyes_gamma.setValue(self.eyes_tracking_param['eye_gamma'])
        self.eyes_gamma.valueChanged.connect(self.on_change)

        self.eyes_contrast = LabeledDoubleSpinBox()
        self.eyes_contrast.setText('contrast')
        self.eyes_contrast.setRange(-10,10)
        self.eyes_contrast.setValue(self.eyes_tracking_param['eye_contrast'])
        self.eyes_contrast.valueChanged.connect(self.on_change)

        self.eyes_min_size_mm = LabeledDoubleSpinBox()
        self.eyes_min_size_mm.setText('min area (mm2)')
        self.eyes_min_size_mm.setRange(0,1000)
        self.eyes_min_size_mm.setValue(self.eyes_tracking_param['eye_size_lo_mm'])
        self.eyes_min_size_mm.valueChanged.connect(self.on_change)

        self.eyes_max_size_mm = LabeledDoubleSpinBox()
        self.eyes_max_size_mm.setText('max area (mm2)')
        self.eyes_max_size_mm.setRange(0,1000)
        self.eyes_max_size_mm.setValue(self.eyes_tracking_param['eye_size_hi_mm'])
        self.eyes_max_size_mm.valueChanged.connect(self.on_change)

        self.eyes_offset_mm = LabeledDoubleSpinBox()
        self.eyes_offset_mm.setText('vertical offset (mm)')
        self.eyes_offset_mm.setRange(-10,10)
        self.eyes_offset_mm.setValue(self.eyes_tracking_param['crop_offset_mm'])
        self.eyes_offset_mm.valueChanged.connect(self.on_change)

        self.eyes_crop_width_mm = LabeledDoubleSpinBox()
        self.eyes_crop_width_mm.setText('crop width')
        self.eyes_crop_width_mm.setRange(0,1000)
        self.eyes_crop_width_mm.setValue(self.eyes_tracking_param['crop_dimension_mm'][0])
        self.eyes_crop_width_mm.valueChanged.connect(self.on_change)

        self.eyes_crop_height_mm = LabeledDoubleSpinBox()
        self.eyes_crop_height_mm.setText('crop height')
        self.eyes_crop_height_mm.setRange(0,1000)
        self.eyes_crop_height_mm.setValue(self.eyes_tracking_param['crop_dimension_mm'][1])
        self.eyes_crop_height_mm.valueChanged.connect(self.on_change)

        self.eyes_blur_sz_mm = LabeledDoubleSpinBox()
        self.eyes_blur_sz_mm.setText('blur size (mm)')
        self.eyes_blur_sz_mm.setRange(0,1000)
        self.eyes_blur_sz_mm.setSingleStep(1/self.eyes_tracking_param['target_pix_per_mm'])
        self.eyes_blur_sz_mm.setValue(self.eyes_tracking_param['blur_sz_mm'])
        self.eyes_blur_sz_mm.valueChanged.connect(self.on_change)

        self.eyes_median_filter_sz_mm = LabeledDoubleSpinBox()
        self.eyes_median_filter_sz_mm.setText('medfilt size (mm)')
        self.eyes_median_filter_sz_mm.setRange(0,1000)
        self.eyes_median_filter_sz_mm.setSingleStep(1/self.eyes_tracking_param['target_pix_per_mm'])
        self.eyes_median_filter_sz_mm.setValue(self.eyes_tracking_param['median_filter_sz_mm'])
        self.eyes_median_filter_sz_mm.valueChanged.connect(self.on_change)

        self.tail_pix_per_mm = LabeledDoubleSpinBox()
        self.tail_pix_per_mm.setText('pix/mm')
        self.tail_pix_per_mm.setRange(0,200)
        self.tail_pix_per_mm.setValue(self.tail_tracking_param['pix_per_mm'])
        self.tail_pix_per_mm.valueChanged.connect(self.on_change)
        
        self.tail_target_pix_per_mm = LabeledDoubleSpinBox()
        self.tail_target_pix_per_mm.setText('target pix/mm')
        self.tail_target_pix_per_mm.setRange(0,200)
        self.tail_target_pix_per_mm.setValue(self.tail_tracking_param['target_pix_per_mm'])
        self.tail_target_pix_per_mm.valueChanged.connect(self.on_change)

        self.tail_brightness = LabeledDoubleSpinBox()
        self.tail_brightness.setText('brightness')
        self.tail_brightness.setRange(-1,1)
        self.tail_brightness.setValue(self.tail_tracking_param['tail_brightness'])
        self.tail_brightness.valueChanged.connect(self.on_change)

        self.tail_gamma = LabeledDoubleSpinBox()
        self.tail_gamma.setText('gamma')
        self.tail_gamma.setRange(-10,10)
        self.tail_gamma.setValue(self.tail_tracking_param['tail_gamma'])
        self.tail_gamma.valueChanged.connect(self.on_change)

        self.tail_contrast = LabeledDoubleSpinBox()
        self.tail_contrast.setText('contrast')
        self.tail_contrast.setRange(-10,10)
        self.tail_contrast.setValue(self.tail_tracking_param['tail_contrast'])
        self.tail_contrast.valueChanged.connect(self.on_change)

        self.tail_ball_radius_mm = LabeledDoubleSpinBox()
        self.tail_ball_radius_mm.setText('ball radius (mm)')
        self.tail_ball_radius_mm.setRange(0,100)
        self.tail_ball_radius_mm.setValue(self.tail_tracking_param['ball_radius_mm'])
        self.tail_ball_radius_mm.valueChanged.connect(self.on_change)

        self.tail_arc_angle_deg = LabeledDoubleSpinBox()
        self.tail_arc_angle_deg.setText('arc angle (deg)')
        self.tail_arc_angle_deg.setRange(0,360)
        self.tail_arc_angle_deg.setValue(self.tail_tracking_param['arc_angle_deg'])
        self.tail_arc_angle_deg.valueChanged.connect(self.on_change)
        
        self.tail_n_points_arc = LabeledDoubleSpinBox()
        self.tail_n_points_arc.setText('arc resolution')
        self.tail_n_points_arc.setRange(0,100)
        self.tail_n_points_arc.setValue(self.tail_tracking_param['n_pts_arc'])
        self.tail_n_points_arc.valueChanged.connect(self.on_change)

        self.n_tail_points = LabeledDoubleSpinBox()
        self.n_tail_points.setText('#tail points')
        self.n_tail_points.setRange(0,100)
        self.n_tail_points.setValue(self.tail_tracking_param['n_tail_points'])
        self.n_tail_points.valueChanged.connect(self.on_change)

        self.n_tail_points_interp = LabeledDoubleSpinBox()
        self.n_tail_points_interp.setText('#tail points interp')
        self.n_tail_points_interp.setRange(0,100_000)
        self.n_tail_points_interp.setValue(self.tail_tracking_param['n_pts_interp'])
        self.n_tail_points_interp.valueChanged.connect(self.on_change)

        self.tail_length_mm = LabeledDoubleSpinBox()
        self.tail_length_mm.setText('tail length (mm)')
        self.tail_length_mm.setRange(0,10)
        self.tail_length_mm.setValue(self.tail_tracking_param['tail_length_mm'])
        self.tail_length_mm.valueChanged.connect(self.on_change)

        self.swim_bladder_mm = LabeledDoubleSpinBox()
        self.swim_bladder_mm.setText('swim bladder offset (mm)')
        self.swim_bladder_mm.setRange(0,10)
        self.swim_bladder_mm.setValue(self.tail_tracking_param['dist_swim_bladder_mm'])
        self.swim_bladder_mm.valueChanged.connect(self.on_change)

        self.tail_offset_mm = LabeledDoubleSpinBox()
        self.tail_offset_mm.setText('vertical offset (mm)')
        self.tail_offset_mm.setRange(0,10)
        self.tail_offset_mm.setValue(self.tail_tracking_param['crop_offset_tail_mm'])
        self.tail_offset_mm.valueChanged.connect(self.on_change)

        self.tail_crop_width_mm = LabeledDoubleSpinBox()
        self.tail_crop_width_mm.setText('crop width (mm)')
        self.tail_crop_width_mm.setRange(0,10)
        self.tail_crop_width_mm.setValue(self.tail_tracking_param['crop_dimension_mm'][0])
        self.tail_crop_width_mm.valueChanged.connect(self.on_change)

        self.tail_crop_height_mm = LabeledDoubleSpinBox()
        self.tail_crop_height_mm.setText('crop height (mm)')
        self.tail_crop_height_mm.setRange(0,10)
        self.tail_crop_height_mm.setValue(self.tail_tracking_param['crop_dimension_mm'][1])
        self.tail_crop_height_mm.valueChanged.connect(self.on_change)

        self.tail_blur_sz_mm = LabeledDoubleSpinBox()
        self.tail_blur_sz_mm.setText('blur size (mm)')
        self.tail_blur_sz_mm.setRange(0,1000)
        self.tail_blur_sz_mm.setSingleStep(1/self.tail_tracking_param['target_pix_per_mm'])
        self.tail_blur_sz_mm.setValue(self.tail_tracking_param['blur_sz_mm'])
        self.tail_blur_sz_mm.valueChanged.connect(self.on_change)

        self.tail_median_filter_sz_mm = LabeledDoubleSpinBox()
        self.tail_median_filter_sz_mm.setText('medfilt size (mm)')
        self.tail_median_filter_sz_mm.setRange(0,1000)
        self.tail_median_filter_sz_mm.setSingleStep(1/self.tail_tracking_param['target_pix_per_mm'])
        self.tail_median_filter_sz_mm.setValue(self.tail_tracking_param['median_filter_sz_mm'])
        self.tail_median_filter_sz_mm.valueChanged.connect(self.on_change)

    def layout_components(self):
        animal = QVBoxLayout()
        animal.addWidget(QLabel('animal'))
        animal.addWidget(self.animal_pix_per_mm)
        animal.addWidget(self.animal_target_pix_per_mm)
        animal.addWidget(self.animal_intensity)
        animal.addWidget(self.animal_brightness)
        animal.addWidget(self.animal_gamma)
        animal.addWidget(self.animal_contrast)
        animal.addWidget(self.animal_min_size_mm)
        animal.addWidget(self.animal_max_size_mm)
        animal.addWidget(self.animal_min_length_mm)
        animal.addWidget(self.animal_max_length_mm)
        animal.addWidget(self.animal_min_width_mm)
        animal.addWidget(self.animal_max_width_mm)
        animal.addWidget(self.animal_blur_sz_mm)
        animal.addWidget(self.animal_median_filter_sz_mm)
        animal.addStretch()

        body = QVBoxLayout()
        body.addWidget(QLabel('body'))
        body.addWidget(self.body_pix_per_mm)
        body.addWidget(self.body_target_pix_per_mm)
        body.addWidget(self.body_intensity)
        body.addWidget(self.body_brightness)
        body.addWidget(self.body_gamma)
        body.addWidget(self.body_contrast)
        body.addWidget(self.body_min_size_mm)
        body.addWidget(self.body_max_size_mm)
        body.addWidget(self.body_min_length_mm)
        body.addWidget(self.body_max_length_mm)
        body.addWidget(self.body_min_width_mm)
        body.addWidget(self.body_max_width_mm)
        body.addWidget(self.body_blur_sz_mm)
        body.addWidget(self.body_median_filter_sz_mm)
        body.addStretch()

        eyes = QVBoxLayout()
        eyes.addWidget(QLabel('eyes'))
        eyes.addWidget(self.eyes_pix_per_mm)
        eyes.addWidget(self.eyes_target_pix_per_mm)
        eyes.addWidget(self.eyes_intensity_lo)
        eyes.addWidget(self.eyes_intensity_hi)
        eyes.addWidget(self.eyes_thresh_resolution)
        eyes.addWidget(self.eyes_brightness)
        eyes.addWidget(self.eyes_gamma)
        eyes.addWidget(self.eyes_contrast)
        eyes.addWidget(self.eyes_min_size_mm)
        eyes.addWidget(self.eyes_max_size_mm)
        eyes.addWidget(self.eyes_offset_mm)
        eyes.addWidget(self.eyes_crop_width_mm)
        eyes.addWidget(self.eyes_crop_height_mm)
        eyes.addWidget(self.eyes_blur_sz_mm)
        eyes.addWidget(self.eyes_median_filter_sz_mm)
        eyes.addStretch()

        tail = QVBoxLayout()
        tail.addWidget(QLabel('tail'))
        tail.addWidget(self.tail_pix_per_mm)
        tail.addWidget(self.tail_target_pix_per_mm)
        tail.addWidget(self.tail_brightness)
        tail.addWidget(self.tail_gamma)
        tail.addWidget(self.tail_contrast)
        tail.addWidget(self.tail_ball_radius_mm)
        tail.addWidget(self.tail_arc_angle_deg)
        tail.addWidget(self.tail_n_points_arc)
        tail.addWidget(self.n_tail_points)
        tail.addWidget(self.n_tail_points_interp)
        tail.addWidget(self.tail_length_mm)
        tail.addWidget(self.swim_bladder_mm) 
        tail.addWidget(self.tail_offset_mm)
        tail.addWidget(self.tail_crop_width_mm)
        tail.addWidget(self.tail_crop_height_mm)
        tail.addWidget(self.tail_blur_sz_mm)
        tail.addWidget(self.tail_median_filter_sz_mm)
        tail.addStretch()

        final = QHBoxLayout(self.window)
        final.addLayout(animal)
        final.addLayout(body)
        final.addLayout(eyes)
        final.addLayout(tail)

    def on_change(self):
        self.updated = True

    def process_data(self, data: None) -> NDArray:
        self.app.processEvents()

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        # send tracking controls
        if self.updated:
            self.updated = False
            res = {}
            for i in range(self.n_tracker_workers):
                res[f'tracker_control_{i}'] = {}
                res[f'tracker_control_{i}']['animal_tracking'] = {}
                res[f'tracker_control_{i}']['body_tracking'] = {}
                res[f'tracker_control_{i}']['eyes_tracking'] = {}
                res[f'tracker_control_{i}']['tail_tracking'] = {}

                res[f'tracker_control_{i}']['animal_tracking']['pix_per_mm']=self.animal_pix_per_mm.value()
                res[f'tracker_control_{i}']['animal_tracking']['target_pix_per_mm']=self.animal_target_pix_per_mm.value()
                res[f'tracker_control_{i}']['animal_tracking']['animal_intensity']=self.animal_intensity.value()
                res[f'tracker_control_{i}']['animal_tracking']['animal_brightness']=self.animal_brightness.value()
                res[f'tracker_control_{i}']['animal_tracking']['animal_gamma']=self.animal_gamma.value()
                res[f'tracker_control_{i}']['animal_tracking']['animal_contrast']=self.animal_contrast.value()
                res[f'tracker_control_{i}']['animal_tracking']['min_animal_size_mm']=self.animal_min_size_mm.value()
                res[f'tracker_control_{i}']['animal_tracking']['max_animal_size_mm']=self.animal_max_size_mm.value()
                res[f'tracker_control_{i}']['animal_tracking']['min_animal_length_mm']=self.animal_min_length_mm.value()
                res[f'tracker_control_{i}']['animal_tracking']['max_animal_length_mm']=self.animal_max_length_mm.value()
                res[f'tracker_control_{i}']['animal_tracking']['min_animal_width_mm']=self.animal_min_width_mm.value()
                res[f'tracker_control_{i}']['animal_tracking']['max_animal_width_mm']=self.animal_max_width_mm.value()
                res[f'tracker_control_{i}']['animal_tracking']['blur_sz_mm']=self.animal_blur_sz_mm.value()
                res[f'tracker_control_{i}']['animal_tracking']['median_filter_sz_mm']=self.animal_median_filter_sz_mm.value()

                res[f'tracker_control_{i}']['body_tracking']['pix_per_mm']=self.body_pix_per_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['target_pix_per_mm']=self.body_target_pix_per_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['body_intensity']=self.body_intensity.value()
                res[f'tracker_control_{i}']['body_tracking']['body_brightness']=self.body_brightness.value()
                res[f'tracker_control_{i}']['body_tracking']['body_gamma']=self.body_gamma.value()
                res[f'tracker_control_{i}']['body_tracking']['body_contrast']=self.body_contrast.value()
                res[f'tracker_control_{i}']['body_tracking']['min_body_size_mm']=self.body_min_size_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['max_body_size_mm']=self.body_max_size_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['min_body_length_mm']=self.body_min_length_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['max_body_length_mm']=self.body_max_length_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['min_body_width_mm']=self.body_min_width_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['max_body_width_mm']=self.body_max_width_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['blur_sz_mm']=self.body_blur_sz_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['median_filter_sz_mm']=self.body_median_filter_sz_mm.value()

                res[f'tracker_control_{i}']['eyes_tracking']['pix_per_mm']=self.eyes_pix_per_mm.value()
                res[f'tracker_control_{i}']['eyes_tracking']['target_pix_per_mm']=self.eyes_target_pix_per_mm.value()
                res[f'tracker_control_{i}']['eyes_tracking']['eye_thresh_lo']=self.eyes_intensity_lo.value()
                res[f'tracker_control_{i}']['eyes_tracking']['eye_thresh_hi']=self.eyes_intensity_hi.value()
                res[f'tracker_control_{i}']['eyes_tracking']['eye_dyntresh_res']=self.eyes_thresh_resolution.value()
                res[f'tracker_control_{i}']['eyes_tracking']['eye_brightness']=self.eyes_brightness.value()
                res[f'tracker_control_{i}']['eyes_tracking']['eye_gamma']=self.eyes_gamma.value()
                res[f'tracker_control_{i}']['eyes_tracking']['eye_contrast']=self.eyes_contrast.value()
                res[f'tracker_control_{i}']['eyes_tracking']['eye_size_lo_mm']=self.eyes_min_size_mm.value()
                res[f'tracker_control_{i}']['eyes_tracking']['eye_size_hi_mm']=self.eyes_max_size_mm.value()
                res[f'tracker_control_{i}']['eyes_tracking']['crop_offset_mm']=self.eyes_offset_mm.value()
                res[f'tracker_control_{i}']['eyes_tracking']['crop_dimension_mm']=(self.eyes_crop_width_mm.value(),self.eyes_crop_height_mm.value())
                res[f'tracker_control_{i}']['eyes_tracking']['blur_sz_mm']=self.eyes_blur_sz_mm.value()
                res[f'tracker_control_{i}']['eyes_tracking']['median_filter_sz_mm']=self.eyes_median_filter_sz_mm.value()

                res[f'tracker_control_{i}']['tail_tracking']['pix_per_mm']=self.tail_pix_per_mm.value()
                res[f'tracker_control_{i}']['tail_tracking']['target_pix_per_mm']=self.tail_target_pix_per_mm.value()
                res[f'tracker_control_{i}']['tail_tracking']['tail_brightness']=self.tail_brightness.value()
                res[f'tracker_control_{i}']['tail_tracking']['tail_gamma']=self.tail_gamma.value()
                res[f'tracker_control_{i}']['tail_tracking']['tail_contrast']=self.tail_contrast.value()
                res[f'tracker_control_{i}']['tail_tracking']['ball_radius_mm']=self.tail_ball_radius_mm.value()
                res[f'tracker_control_{i}']['tail_tracking']['arc_angle_deg']=self.tail_arc_angle_deg.value()
                res[f'tracker_control_{i}']['tail_tracking']['n_pts_arc']=self.tail_n_points_arc.value()
                res[f'tracker_control_{i}']['tail_tracking']['n_tail_points']=self.n_tail_points.value()
                res[f'tracker_control_{i}']['tail_tracking']['n_pts_interp']=self.n_tail_points_interp.value()
                res[f'tracker_control_{i}']['tail_tracking']['tail_length_mm']=self.tail_length_mm.value()
                res[f'tracker_control_{i}']['tail_tracking']['dist_swim_bladder_mm']=self.swim_bladder_mm.value()
                res[f'tracker_control_{i}']['tail_tracking']['crop_dimension_mm']=(self.tail_crop_width_mm.value(),self.tail_crop_height_mm.value())
                res[f'tracker_control_{i}']['tail_tracking']['crop_offset_tail_mm']=self.tail_offset_mm.value()
                res[f'tracker_control_{i}']['tail_tracking']['blur_sz_mm']=self.tail_blur_sz_mm.value()
                res[f'tracker_control_{i}']['tail_tracking']['median_filter_sz_mm']=self.tail_median_filter_sz_mm.value()
            return res
