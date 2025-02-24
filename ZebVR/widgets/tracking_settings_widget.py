from typing import Dict
from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QGroupBox,
    QFileDialog,
    QPushButton
)
from qt_widgets import LabeledDoubleSpinBox, LabeledSpinBox, LabeledComboBox
import json
from pathlib import Path

# TODO add assignment widget

class TrackerWidget(QWidget):

    def __init__(
            self,
            settings_file: Path = Path('tracking.json'),
            *args,
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.updated = False
        self.declare_components()
        self.layout_components()
        self.setWindowTitle('Tracking controls')

        if settings_file.exists():
            self.load_from_file(settings_file)

    def declare_components(self):

        self.assignment_choice = LabeledComboBox()
        self.assignment_choice.setText('Assignment:')
        self.assignment_choice.addItem('ROI')
        self.assignment_choice.addItem('Hungarian')
        self.assignment_choice.currentIndexChanged.connect(self.on_change)      
        self.assignment_choice.setEnabled(False)

        self.animal_num_animals = LabeledSpinBox()
        self.animal_num_animals.setText('#animals')
        self.animal_num_animals.setRange(0,100)
        self.animal_num_animals.setSingleStep(1)
        self.animal_num_animals.setValue(1)
        self.animal_num_animals.valueChanged.connect(self.on_change)
        self.animal_num_animals.setEnabled(False)
    
        self.animal_pix_per_mm = LabeledDoubleSpinBox()
        self.animal_pix_per_mm.setText('pix/mm')
        self.animal_pix_per_mm.setRange(1,200)
        self.animal_pix_per_mm.setValue(50)
        self.animal_pix_per_mm.setSingleStep(0.25)
        self.animal_pix_per_mm.valueChanged.connect(self.on_change)

        self.animal_target_pix_per_mm = LabeledDoubleSpinBox()
        self.animal_target_pix_per_mm.setText('target pix/mm')
        self.animal_target_pix_per_mm.setRange(1,200)
        self.animal_target_pix_per_mm.setValue(5)
        self.animal_target_pix_per_mm.setSingleStep(0.25)
        self.animal_target_pix_per_mm.valueChanged.connect(self.on_change)

        self.animal_intensity = LabeledDoubleSpinBox()
        self.animal_intensity.setText('intensity')
        self.animal_intensity.setRange(0,1)
        self.animal_intensity.setSingleStep(0.025)
        self.animal_intensity.setValue(0.2)
        self.animal_intensity.valueChanged.connect(self.on_change)

        self.animal_brightness = LabeledDoubleSpinBox()
        self.animal_brightness.setText('brightness')
        self.animal_brightness.setRange(-1,1)
        self.animal_brightness.setSingleStep(0.025)
        self.animal_brightness.setValue(0.0)
        self.animal_brightness.valueChanged.connect(self.on_change)

        self.animal_gamma = LabeledDoubleSpinBox()
        self.animal_gamma.setText('gamma')
        self.animal_gamma.setRange(0.05,10)
        self.animal_gamma.setSingleStep(0.05)
        self.animal_gamma.setValue(1.0)
        self.animal_gamma.valueChanged.connect(self.on_change)
        
        self.animal_contrast = LabeledDoubleSpinBox()
        self.animal_contrast.setText('contrast')
        self.animal_contrast.setRange(-10,10)
        self.animal_contrast.setSingleStep(0.05)
        self.animal_contrast.setValue(1.0)
        self.animal_contrast.valueChanged.connect(self.on_change)

        self.animal_min_size_mm = LabeledDoubleSpinBox()
        self.animal_min_size_mm.setText('min area (mm2)')
        self.animal_min_size_mm.setRange(0,100_000)
        self.animal_min_size_mm.setSingleStep(1.0)
        self.animal_min_size_mm.setValue(2.0)
        self.animal_min_size_mm.valueChanged.connect(self.on_change)

        self.animal_max_size_mm = LabeledDoubleSpinBox()
        self.animal_max_size_mm.setText('max area (mm2)')
        self.animal_max_size_mm.setRange(0,100_000)
        self.animal_max_size_mm.setSingleStep(1.0)
        self.animal_max_size_mm.setValue(300.0)
        self.animal_max_size_mm.valueChanged.connect(self.on_change)

        self.animal_min_length_mm = LabeledDoubleSpinBox()
        self.animal_min_length_mm.setText('min length (mm)')
        self.animal_min_length_mm.setRange(0,100_000)
        self.animal_min_length_mm.setSingleStep(1.0)
        self.animal_min_length_mm.setValue(0.0)
        self.animal_min_length_mm.valueChanged.connect(self.on_change)

        self.animal_max_length_mm = LabeledDoubleSpinBox()
        self.animal_max_length_mm.setText('max length (mm)')
        self.animal_max_length_mm.setRange(0,100_000)
        self.animal_max_length_mm.setSingleStep(1.0)
        self.animal_max_length_mm.setValue(0.0)
        self.animal_max_length_mm.valueChanged.connect(self.on_change)

        self.animal_min_width_mm = LabeledDoubleSpinBox()
        self.animal_min_width_mm.setText('min width (mm)')
        self.animal_min_width_mm.setRange(0,100_000)
        self.animal_min_width_mm.setSingleStep(1.0)
        self.animal_min_width_mm.setValue(0.0)
        self.animal_min_width_mm.valueChanged.connect(self.on_change)

        self.animal_max_width_mm = LabeledDoubleSpinBox()
        self.animal_max_width_mm.setText('max width (mm)')
        self.animal_max_width_mm.setRange(0,100_000)
        self.animal_max_width_mm.setSingleStep(1.0)
        self.animal_max_width_mm.setValue(0.0)
        self.animal_max_width_mm.valueChanged.connect(self.on_change)

        self.animal_blur_sz_mm = LabeledDoubleSpinBox()
        self.animal_blur_sz_mm.setText('blur size (mm)')
        self.animal_blur_sz_mm.setRange(0,1000)
        self.animal_blur_sz_mm.setSingleStep(0.1)
        self.animal_blur_sz_mm.setValue(0.60)
        self.animal_blur_sz_mm.valueChanged.connect(self.on_change)
        
        self.animal_median_filter_sz_mm = LabeledDoubleSpinBox()
        self.animal_median_filter_sz_mm.setText('medfilt size (mm)')
        self.animal_median_filter_sz_mm.setRange(0,1000)
        self.animal_median_filter_sz_mm.setSingleStep(0.1)
        self.animal_median_filter_sz_mm.setValue(0.0)
        self.animal_median_filter_sz_mm.valueChanged.connect(self.on_change)

        self.animal_downsample_ratio = LabeledDoubleSpinBox()
        self.animal_downsample_ratio.setText('downsample ratio')
        self.animal_downsample_ratio.setRange(0.1,1.0)
        self.animal_downsample_ratio.setSingleStep(0.05)
        self.animal_downsample_ratio.setValue(0.25)
        self.animal_downsample_ratio.valueChanged.connect(self.on_change)

        self.body_pix_per_mm = LabeledDoubleSpinBox()
        self.body_pix_per_mm.setText('pix/mm')
        self.body_pix_per_mm.setRange(1,200)
        self.body_pix_per_mm.setSingleStep(0.25)
        self.body_pix_per_mm.setValue(50)
        self.body_pix_per_mm.valueChanged.connect(self.on_change)
        
        self.body_target_pix_per_mm = LabeledDoubleSpinBox()
        self.body_target_pix_per_mm.setText('target pix/mm')
        self.body_target_pix_per_mm.setRange(1,200)
        self.body_target_pix_per_mm.setSingleStep(0.25)
        self.body_target_pix_per_mm.setValue(7.5)
        self.body_target_pix_per_mm.valueChanged.connect(self.on_change)
        
        self.body_intensity = LabeledDoubleSpinBox()
        self.body_intensity.setText('intensity')
        self.body_intensity.setRange(0,1)
        self.body_intensity.setSingleStep(0.025)
        self.body_intensity.setValue(0.2)
        self.body_intensity.valueChanged.connect(self.on_change)

        self.body_brightness = LabeledDoubleSpinBox()
        self.body_brightness.setText('brightness')
        self.body_brightness.setRange(-1,1)
        self.body_brightness.setSingleStep(0.025)
        self.body_brightness.setValue(0.0)
        self.body_brightness.valueChanged.connect(self.on_change)

        self.body_gamma = LabeledDoubleSpinBox()
        self.body_gamma.setText('gamma')
        self.body_gamma.setRange(0.05,10)
        self.body_gamma.setSingleStep(0.05)
        self.body_gamma.setValue(1.0)
        self.body_gamma.valueChanged.connect(self.on_change)

        self.body_contrast = LabeledDoubleSpinBox()
        self.body_contrast.setText('contrast')
        self.body_contrast.setRange(-10,10)
        self.body_contrast.setSingleStep(0.05)
        self.body_contrast.setValue(1.0)
        self.body_contrast.valueChanged.connect(self.on_change)

        self.body_min_size_mm = LabeledDoubleSpinBox()
        self.body_min_size_mm.setText('min area (mm2)')
        self.body_min_size_mm.setRange(0,100_000)
        self.body_min_size_mm.setSingleStep(1.0)
        self.body_min_size_mm.setValue(2.0)
        self.body_min_size_mm.valueChanged.connect(self.on_change)

        self.body_max_size_mm = LabeledDoubleSpinBox()
        self.body_max_size_mm.setText('max area (mm2)')
        self.body_max_size_mm.setRange(0,100_000)
        self.body_max_size_mm.setSingleStep(1.0)
        self.body_max_size_mm.setValue(300)
        self.body_max_size_mm.valueChanged.connect(self.on_change)

        self.body_min_length_mm = LabeledDoubleSpinBox()
        self.body_min_length_mm.setText('min length (mm)')
        self.body_min_length_mm.setRange(0,100_000)
        self.body_min_length_mm.setSingleStep(1.0)
        self.body_min_length_mm.setValue(0.0)
        self.body_min_length_mm.valueChanged.connect(self.on_change)

        self.body_max_length_mm = LabeledDoubleSpinBox()
        self.body_max_length_mm.setText('max length (mm)')
        self.body_max_length_mm.setRange(0,100_000)
        self.body_max_length_mm.setSingleStep(1.0)
        self.body_max_length_mm.setValue(0.0)
        self.body_max_length_mm.valueChanged.connect(self.on_change)

        self.body_min_width_mm = LabeledDoubleSpinBox()
        self.body_min_width_mm.setText('min width (mm)')
        self.body_min_width_mm.setRange(0,100_000)
        self.body_min_width_mm.setSingleStep(1.0)
        self.body_min_width_mm.setValue(0.0)
        self.body_min_width_mm.valueChanged.connect(self.on_change)

        self.body_max_width_mm = LabeledDoubleSpinBox()
        self.body_max_width_mm.setText('max width (mm)')
        self.body_max_width_mm.setRange(0,100_000)
        self.body_max_width_mm.setSingleStep(1.0)
        self.body_max_width_mm.setValue(0.0)
        self.body_max_width_mm.valueChanged.connect(self.on_change)

        self.body_crop_width_mm = LabeledDoubleSpinBox()
        self.body_crop_width_mm.setText('crop width')
        self.body_crop_width_mm.setRange(0.5,100)
        self.body_crop_width_mm.setSingleStep(0.05)
        self.body_crop_width_mm.setValue(9.0)
        self.body_crop_width_mm.valueChanged.connect(self.on_change)

        self.body_crop_height_mm = LabeledDoubleSpinBox()
        self.body_crop_height_mm.setText('crop height')
        self.body_crop_height_mm.setRange(0.5,100)
        self.body_crop_height_mm.setSingleStep(0.05)
        self.body_crop_height_mm.setValue(9.0)
        self.body_crop_height_mm.valueChanged.connect(self.on_change)

        self.body_blur_sz_mm = LabeledDoubleSpinBox()
        self.body_blur_sz_mm.setText('blur size (mm)')
        self.body_blur_sz_mm.setRange(0,1000)
        self.body_blur_sz_mm.setSingleStep(0.1)
        self.body_blur_sz_mm.setValue(0.60)
        self.body_blur_sz_mm.valueChanged.connect(self.on_change)

        self.body_median_filter_sz_mm = LabeledDoubleSpinBox()
        self.body_median_filter_sz_mm.setText('medfilt size (mm)')
        self.body_median_filter_sz_mm.setRange(0,1000)
        self.body_median_filter_sz_mm.setSingleStep(0.1)
        self.body_median_filter_sz_mm.setValue(0.0)
        self.body_median_filter_sz_mm.valueChanged.connect(self.on_change)

        self.eyes_pix_per_mm = LabeledDoubleSpinBox()
        self.eyes_pix_per_mm.setText('pix/mm')
        self.eyes_pix_per_mm.setRange(1,200)
        self.eyes_pix_per_mm.setSingleStep(0.25)
        self.eyes_pix_per_mm.setValue(50)
        self.eyes_pix_per_mm.valueChanged.connect(self.on_change)

        self.eyes_target_pix_per_mm = LabeledDoubleSpinBox()
        self.eyes_target_pix_per_mm.setText('target pix/mm')
        self.eyes_target_pix_per_mm.setRange(1,200)
        self.eyes_target_pix_per_mm.setSingleStep(0.25)
        self.eyes_target_pix_per_mm.setValue(40)
        self.eyes_target_pix_per_mm.valueChanged.connect(self.on_change)
        
        self.eyes_intensity_lo = LabeledDoubleSpinBox()
        self.eyes_intensity_lo.setText('thresh low')
        self.eyes_intensity_lo.setRange(0,1)
        self.eyes_intensity_lo.setSingleStep(0.025)
        self.eyes_intensity_lo.setValue(0.2)
        self.eyes_intensity_lo.valueChanged.connect(self.on_change)

        self.eyes_intensity_hi = LabeledDoubleSpinBox()
        self.eyes_intensity_hi.setText('thresh high')
        self.eyes_intensity_hi.setRange(0,1)
        self.eyes_intensity_hi.setSingleStep(0.025)
        self.eyes_intensity_hi.setValue(0.8)
        self.eyes_intensity_hi.valueChanged.connect(self.on_change)

        self.eyes_thresh_resolution = LabeledSpinBox()
        self.eyes_thresh_resolution.setText('thresh steps')
        self.eyes_thresh_resolution.setSingleStep(1)
        self.eyes_thresh_resolution.setRange(1,100)
        self.eyes_thresh_resolution.setValue(10)
        self.eyes_thresh_resolution.valueChanged.connect(self.on_change)

        self.eyes_brightness = LabeledDoubleSpinBox()
        self.eyes_brightness.setText('brightness')
        self.eyes_brightness.setRange(-1,1)
        self.eyes_brightness.setSingleStep(0.025)
        self.eyes_brightness.setValue(0.0)
        self.eyes_brightness.valueChanged.connect(self.on_change)

        self.eyes_gamma = LabeledDoubleSpinBox()
        self.eyes_gamma.setText('gamma')
        self.eyes_gamma.setRange(0.05,10)
        self.eyes_gamma.setSingleStep(0.05)
        self.eyes_gamma.setValue(1.0)
        self.eyes_gamma.valueChanged.connect(self.on_change)

        self.eyes_contrast = LabeledDoubleSpinBox()
        self.eyes_contrast.setText('contrast')
        self.eyes_contrast.setRange(-10,10)
        self.eyes_contrast.setSingleStep(0.05)
        self.eyes_contrast.setValue(1.0)
        self.eyes_contrast.valueChanged.connect(self.on_change)

        self.eyes_min_size_mm = LabeledDoubleSpinBox()
        self.eyes_min_size_mm.setText('min area (mm2)')
        self.eyes_min_size_mm.setRange(0,1000)
        self.eyes_min_size_mm.setSingleStep(1.0)
        self.eyes_min_size_mm.setValue(2.0)
        self.eyes_min_size_mm.valueChanged.connect(self.on_change)

        self.eyes_max_size_mm = LabeledDoubleSpinBox()
        self.eyes_max_size_mm.setText('max area (mm2)')
        self.eyes_max_size_mm.setRange(0,1000)
        self.eyes_max_size_mm.setSingleStep(1.0)
        self.eyes_max_size_mm.setValue(30.0)
        self.eyes_max_size_mm.valueChanged.connect(self.on_change)

        self.eyes_offset_mm = LabeledDoubleSpinBox()
        self.eyes_offset_mm.setText('vertical offset (mm)')
        self.eyes_offset_mm.setRange(-10,10)
        self.eyes_offset_mm.setSingleStep(0.025)
        self.eyes_offset_mm.setValue(0.0)
        self.eyes_offset_mm.valueChanged.connect(self.on_change)

        self.eyes_crop_width_mm = LabeledDoubleSpinBox()
        self.eyes_crop_width_mm.setText('crop width')
        self.eyes_crop_width_mm.setRange(0.2,100)
        self.eyes_crop_width_mm.setSingleStep(0.05)
        self.eyes_crop_width_mm.setValue(5)
        self.eyes_crop_width_mm.valueChanged.connect(self.on_change)

        self.eyes_crop_height_mm = LabeledDoubleSpinBox()
        self.eyes_crop_height_mm.setText('crop height')
        self.eyes_crop_height_mm.setRange(0.2,100)
        self.eyes_crop_height_mm.setSingleStep(0.05)
        self.eyes_crop_height_mm.setValue(5)
        self.eyes_crop_height_mm.valueChanged.connect(self.on_change)

        self.eyes_blur_sz_mm = LabeledDoubleSpinBox()
        self.eyes_blur_sz_mm.setText('blur size (mm)')
        self.eyes_blur_sz_mm.setRange(0,1000)
        self.eyes_blur_sz_mm.setSingleStep(0.1)
        self.eyes_blur_sz_mm.setValue(0.1)
        self.eyes_blur_sz_mm.valueChanged.connect(self.on_change)

        self.eyes_median_filter_sz_mm = LabeledDoubleSpinBox()
        self.eyes_median_filter_sz_mm.setText('medfilt size (mm)')
        self.eyes_median_filter_sz_mm.setRange(0,1000)
        self.eyes_median_filter_sz_mm.setSingleStep(0.1)
        self.eyes_median_filter_sz_mm.setValue(0.0)
        self.eyes_median_filter_sz_mm.valueChanged.connect(self.on_change)

        self.tail_pix_per_mm = LabeledDoubleSpinBox()
        self.tail_pix_per_mm.setText('pix/mm')
        self.tail_pix_per_mm.setRange(1,200)
        self.tail_pix_per_mm.setSingleStep(0.25)
        self.tail_pix_per_mm.setValue(50)
        self.tail_pix_per_mm.valueChanged.connect(self.on_change)
        
        self.tail_target_pix_per_mm = LabeledDoubleSpinBox()
        self.tail_target_pix_per_mm.setText('target pix/mm')
        self.tail_target_pix_per_mm.setRange(1,200)
        self.tail_target_pix_per_mm.setSingleStep(0.25)
        self.tail_target_pix_per_mm.setValue(20)
        self.tail_target_pix_per_mm.valueChanged.connect(self.on_change)

        self.tail_brightness = LabeledDoubleSpinBox()
        self.tail_brightness.setText('brightness')
        self.tail_brightness.setRange(-1,1)
        self.tail_brightness.setSingleStep(0.025)
        self.tail_brightness.setValue(0.0)
        self.tail_brightness.valueChanged.connect(self.on_change)

        self.tail_gamma = LabeledDoubleSpinBox()
        self.tail_gamma.setText('gamma')
        self.tail_gamma.setRange(0.05,10)
        self.tail_gamma.setSingleStep(0.05)
        self.tail_gamma.setValue(1.0)
        self.tail_gamma.valueChanged.connect(self.on_change)

        self.tail_contrast = LabeledDoubleSpinBox()
        self.tail_contrast.setText('contrast')
        self.tail_contrast.setRange(-10,10)
        self.tail_contrast.setSingleStep(0.05)
        self.tail_contrast.setValue(1.0)
        self.tail_contrast.valueChanged.connect(self.on_change)

        self.tail_ball_radius_mm = LabeledDoubleSpinBox()
        self.tail_ball_radius_mm.setText('ball radius (mm)')
        self.tail_ball_radius_mm.setRange(0.05,10)
        self.tail_ball_radius_mm.setSingleStep(0.01)
        self.tail_ball_radius_mm.setValue(0.15)
        self.tail_ball_radius_mm.valueChanged.connect(self.on_change)

        self.tail_arc_angle_deg = LabeledDoubleSpinBox()
        self.tail_arc_angle_deg.setText('arc angle (deg)')
        self.tail_arc_angle_deg.setRange(1,360)
        self.tail_arc_angle_deg.setSingleStep(1.0)
        self.tail_arc_angle_deg.setValue(90)
        self.tail_arc_angle_deg.valueChanged.connect(self.on_change)
        
        self.tail_n_points_arc = LabeledSpinBox()
        self.tail_n_points_arc.setText('arc resolution')
        self.tail_n_points_arc.setRange(2,100)
        self.tail_n_points_arc.setSingleStep(1)
        self.tail_n_points_arc.setValue(20)
        self.tail_n_points_arc.valueChanged.connect(self.on_change)

        self.n_tail_points = LabeledSpinBox()
        self.n_tail_points.setText('#tail points')
        self.n_tail_points.setRange(3,100)
        self.n_tail_points.setSingleStep(1)
        self.n_tail_points.setValue(6)
        self.n_tail_points.valueChanged.connect(self.on_change)

        self.n_tail_points_interp = LabeledSpinBox()
        self.n_tail_points_interp.setText('#tail points interp')
        self.n_tail_points_interp.setRange(2,100)
        self.n_tail_points_interp.setSingleStep(1)
        self.n_tail_points_interp.setValue(40)
        self.n_tail_points_interp.valueChanged.connect(self.on_change)
        self.n_tail_points_interp.setEnabled(False) # This cant change because it would change columns in output csv 

        self.tail_length_mm = LabeledDoubleSpinBox()
        self.tail_length_mm.setText('tail length (mm)')
        self.tail_length_mm.setRange(0.5,10)
        self.tail_length_mm.setSingleStep(0.05)
        self.tail_length_mm.setValue(3.5)
        self.tail_length_mm.valueChanged.connect(self.on_change)

        self.swim_bladder_mm = LabeledDoubleSpinBox()
        self.swim_bladder_mm.setText('swim bladder offset (mm)')
        self.swim_bladder_mm.setRange(0,10)
        self.swim_bladder_mm.setSingleStep(0.025)
        self.swim_bladder_mm.setValue(0)
        self.swim_bladder_mm.valueChanged.connect(self.on_change)

        self.tail_offset_mm = LabeledDoubleSpinBox()
        self.tail_offset_mm.setText('vertical offset (mm)')
        self.tail_offset_mm.setRange(0,10)
        self.tail_offset_mm.setSingleStep(0.025)
        self.tail_offset_mm.setValue(2.0)
        self.tail_offset_mm.valueChanged.connect(self.on_change)

        self.tail_crop_width_mm = LabeledDoubleSpinBox()
        self.tail_crop_width_mm.setText('crop width (mm)')
        self.tail_crop_width_mm.setRange(0.5,10)
        self.tail_crop_width_mm.setSingleStep(0.05)
        self.tail_crop_width_mm.setValue(5)
        self.tail_crop_width_mm.valueChanged.connect(self.on_change)

        self.tail_crop_height_mm = LabeledDoubleSpinBox()
        self.tail_crop_height_mm.setText('crop height (mm)')
        self.tail_crop_height_mm.setRange(0.5,10)
        self.tail_crop_height_mm.setSingleStep(0.05)
        self.tail_crop_height_mm.setValue(5)
        self.tail_crop_height_mm.valueChanged.connect(self.on_change)

        self.tail_blur_sz_mm = LabeledDoubleSpinBox()
        self.tail_blur_sz_mm.setText('blur size (mm)')
        self.tail_blur_sz_mm.setRange(0,1000)
        self.tail_blur_sz_mm.setSingleStep(0.1)
        self.tail_blur_sz_mm.setValue(0.1)
        self.tail_blur_sz_mm.valueChanged.connect(self.on_change)

        self.tail_median_filter_sz_mm = LabeledDoubleSpinBox()
        self.tail_median_filter_sz_mm.setText('medfilt size (mm)')
        self.tail_median_filter_sz_mm.setRange(0,1000)
        self.tail_median_filter_sz_mm.setSingleStep(0.1)
        self.tail_median_filter_sz_mm.setValue(0.1)
        self.tail_median_filter_sz_mm.valueChanged.connect(self.on_change)

        self.btn_load = QPushButton('load')
        self.btn_load.clicked.connect(self.load)

        self.btn_save = QPushButton('save')
        self.btn_save.clicked.connect(self.save)

    def layout_components(self):

        self.group_animal = QGroupBox('animal')
        animal = QVBoxLayout()
        animal.addWidget(self.animal_num_animals)
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
        animal.addWidget(self.animal_downsample_ratio)
        animal.addStretch()
        self.group_animal.setLayout(animal)

        self.group_body = QGroupBox('body')
        self.group_body.setCheckable(True)
        self.group_body.setChecked(True)
        self.group_body.toggled.connect(self.on_change)

        body = QVBoxLayout()
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
        body.addWidget(self.body_crop_width_mm)
        body.addWidget(self.body_crop_height_mm)
        body.addWidget(self.body_blur_sz_mm)
        body.addWidget(self.body_median_filter_sz_mm)
        body.addStretch()
        self.group_body.setLayout(body)

        self.group_eyes = QGroupBox('eyes')
        self.group_eyes.setCheckable(True)
        self.group_eyes.setChecked(True)
        self.group_eyes.toggled.connect(self.on_change)

        eyes = QVBoxLayout()
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
        self.group_eyes.setLayout(eyes)

        self.group_tail = QGroupBox('tail')
        self.group_tail.setCheckable(True)
        self.group_tail.setChecked(True)
        self.group_tail.toggled.connect(self.on_change)

        tail = QVBoxLayout()
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
        self.group_tail.setLayout(tail)

        io_layout = QHBoxLayout()
        io_layout.addStretch()
        io_layout.addWidget(self.btn_load)
        io_layout.addWidget(self.btn_save)

        groups = QHBoxLayout()
        groups.addWidget(self.group_animal)
        groups.addWidget(self.group_body)
        groups.addWidget(self.group_eyes)
        groups.addWidget(self.group_tail)
        
        final = QVBoxLayout(self)
        final.addWidget(self.assignment_choice)
        final.addLayout(groups)
        final.addLayout(io_layout)

    def on_change(self):
        
        if not self.group_body.isChecked():
            self.group_eyes.setChecked(False)
            self.group_tail.setChecked(False)

        self.updated = True

    def is_updated(self) -> bool:
        return self.updated
    
    def set_updated(self, updated:bool) -> None:
        self.updated = updated

    def save(self):
        state = self.get_state()
        
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Save file",
            "tracking.json",
            "JSON file (*.json)"
        )

        with open(filename, 'w') as fp:
            json.dump(state, fp)

    def load(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "Load file",
            "protocol.json",
            "JSON file (*.json)"
        )
        self.load_from_file(filename)
        

    def load_from_file(self, filename):

        with open(filename, 'r') as fp:
            state = json.load(fp)

        self.set_state(state)
        self.updated = True

    def get_state(self) -> Dict:
        state = {}
            
        state['assignment'] = self.assignment_choice.currentText()

        state['body'] = self.group_body.isChecked()
        state['eyes'] = self.group_eyes.isChecked()
        state['tail'] = self.group_tail.isChecked() 

        state['animal_tracking'] = {}
        state['animal_tracking']['pix_per_mm']=self.animal_pix_per_mm.value()
        state['animal_tracking']['target_pix_per_mm']=self.animal_target_pix_per_mm.value()
        state['animal_tracking']['animal_intensity']=self.animal_intensity.value()
        state['animal_tracking']['animal_brightness']=self.animal_brightness.value()
        state['animal_tracking']['animal_gamma']=self.animal_gamma.value()
        state['animal_tracking']['animal_contrast']=self.animal_contrast.value()
        state['animal_tracking']['min_animal_size_mm']=self.animal_min_size_mm.value()
        state['animal_tracking']['max_animal_size_mm']=self.animal_max_size_mm.value()
        state['animal_tracking']['min_animal_length_mm']=self.animal_min_length_mm.value()
        state['animal_tracking']['max_animal_length_mm']=self.animal_max_length_mm.value()
        state['animal_tracking']['min_animal_width_mm']=self.animal_min_width_mm.value()
        state['animal_tracking']['max_animal_width_mm']=self.animal_max_width_mm.value()
        state['animal_tracking']['blur_sz_mm']=self.animal_blur_sz_mm.value()
        state['animal_tracking']['median_filter_sz_mm']=self.animal_median_filter_sz_mm.value()
        state['animal_tracking']['downsample_fullres']=self.animal_downsample_ratio.value()
        state['animal_tracking']['num_animals']=self.animal_num_animals.value()
        
        state['body_tracking_enabled']=self.group_body.isChecked()
        state['body_tracking'] = {}
        state['body_tracking']['pix_per_mm']=self.body_pix_per_mm.value()
        state['body_tracking']['target_pix_per_mm']=self.body_target_pix_per_mm.value()
        state['body_tracking']['body_intensity']=self.body_intensity.value()
        state['body_tracking']['body_brightness']=self.body_brightness.value()
        state['body_tracking']['body_gamma']=self.body_gamma.value()
        state['body_tracking']['body_contrast']=self.body_contrast.value()
        state['body_tracking']['min_body_size_mm']=self.body_min_size_mm.value()
        state['body_tracking']['max_body_size_mm']=self.body_max_size_mm.value()
        state['body_tracking']['min_body_length_mm']=self.body_min_length_mm.value()
        state['body_tracking']['max_body_length_mm']=self.body_max_length_mm.value()
        state['body_tracking']['min_body_width_mm']=self.body_min_width_mm.value()
        state['body_tracking']['max_body_width_mm']=self.body_max_width_mm.value()
        state['body_tracking']['crop_dimension_mm']=(self.body_crop_width_mm.value(),self.body_crop_height_mm.value())
        state['body_tracking']['blur_sz_mm']=self.body_blur_sz_mm.value()
        state['body_tracking']['median_filter_sz_mm']=self.body_median_filter_sz_mm.value()

        state['eyes_tracking_enabled']=self.group_eyes.isChecked()
        state['eyes_tracking'] = {}
        state['eyes_tracking']['pix_per_mm']=self.eyes_pix_per_mm.value()
        state['eyes_tracking']['target_pix_per_mm']=self.eyes_target_pix_per_mm.value()
        state['eyes_tracking']['eye_thresh_lo']=self.eyes_intensity_lo.value()
        state['eyes_tracking']['eye_thresh_hi']=self.eyes_intensity_hi.value()
        state['eyes_tracking']['eye_dyntresh_res']=self.eyes_thresh_resolution.value()
        state['eyes_tracking']['eye_brightness']=self.eyes_brightness.value()
        state['eyes_tracking']['eye_gamma']=self.eyes_gamma.value()
        state['eyes_tracking']['eye_contrast']=self.eyes_contrast.value()
        state['eyes_tracking']['eye_size_lo_mm']=self.eyes_min_size_mm.value()
        state['eyes_tracking']['eye_size_hi_mm']=self.eyes_max_size_mm.value()
        state['eyes_tracking']['crop_offset_mm']=self.eyes_offset_mm.value()
        state['eyes_tracking']['crop_dimension_mm']=(self.eyes_crop_width_mm.value(),self.eyes_crop_height_mm.value())
        state['eyes_tracking']['blur_sz_mm']=self.eyes_blur_sz_mm.value()
        state['eyes_tracking']['median_filter_sz_mm']=self.eyes_median_filter_sz_mm.value()

        state['tail_tracking_enabled']=self.group_tail.isChecked()
        state['tail_tracking'] = {}
        state['tail_tracking']['pix_per_mm']=self.tail_pix_per_mm.value()
        state['tail_tracking']['target_pix_per_mm']=self.tail_target_pix_per_mm.value()
        state['tail_tracking']['tail_brightness']=self.tail_brightness.value()
        state['tail_tracking']['tail_gamma']=self.tail_gamma.value()
        state['tail_tracking']['tail_contrast']=self.tail_contrast.value()
        state['tail_tracking']['ball_radius_mm']=self.tail_ball_radius_mm.value()
        state['tail_tracking']['arc_angle_deg']=self.tail_arc_angle_deg.value()
        state['tail_tracking']['n_pts_arc']=self.tail_n_points_arc.value()
        state['tail_tracking']['n_tail_points']=self.n_tail_points.value()
        state['tail_tracking']['n_pts_interp']=self.n_tail_points_interp.value()
        state['tail_tracking']['tail_length_mm']=self.tail_length_mm.value()
        state['tail_tracking']['dist_swim_bladder_mm']=self.swim_bladder_mm.value()
        state['tail_tracking']['crop_dimension_mm']=(self.tail_crop_width_mm.value(),self.tail_crop_height_mm.value())
        state['tail_tracking']['crop_offset_tail_mm']=self.tail_offset_mm.value()
        state['tail_tracking']['blur_sz_mm']=self.tail_blur_sz_mm.value()
        state['tail_tracking']['median_filter_sz_mm']=self.tail_median_filter_sz_mm.value()

        return state

    def set_state(self, state:Dict) -> None:

        self.assignment_choice.setCurrentText(state['assignment'])

        self.group_body.setChecked(state['body'])
        self.group_eyes.setChecked(state['eyes'])
        self.group_tail.setChecked(state['tail'])  

        self.animal_pix_per_mm.setValue(state['animal_tracking']['pix_per_mm'])
        self.animal_target_pix_per_mm.setValue(state['animal_tracking']['target_pix_per_mm'])
        self.animal_intensity.setValue(state['animal_tracking']['animal_intensity'])
        self.animal_brightness.setValue(state['animal_tracking']['animal_brightness'])
        self.animal_gamma.setValue(state['animal_tracking']['animal_gamma'])
        self.animal_contrast.setValue(state['animal_tracking']['animal_contrast'])
        self.animal_min_size_mm.setValue(state['animal_tracking']['min_animal_size_mm'])
        self.animal_max_size_mm.setValue(state['animal_tracking']['max_animal_size_mm'])
        self.animal_min_length_mm.setValue(state['animal_tracking']['min_animal_length_mm'])
        self.animal_max_length_mm.setValue(state['animal_tracking']['max_animal_length_mm'])
        self.animal_min_width_mm.setValue(state['animal_tracking']['min_animal_width_mm'])
        self.animal_max_width_mm.setValue(state['animal_tracking']['max_animal_width_mm'])
        self.animal_blur_sz_mm.setValue(state['animal_tracking']['blur_sz_mm'])
        self.animal_median_filter_sz_mm.setValue(state['animal_tracking']['median_filter_sz_mm'])
        self.animal_num_animals.setValue(state['animal_tracking']['num_animals'])
        self.animal_downsample_ratio.setValue(state['animal_tracking']['downsample_fullres'])
        
        self.group_body.setChecked(state['body_tracking_enabled'])
        self.body_pix_per_mm.setValue(state['body_tracking']['pix_per_mm'])
        self.body_target_pix_per_mm.setValue(state['body_tracking']['target_pix_per_mm'])
        self.body_intensity.setValue(state['body_tracking']['body_intensity'])
        self.body_brightness.setValue(state['body_tracking']['body_brightness'])
        self.body_gamma.setValue(state['body_tracking']['body_gamma'])
        self.body_contrast.setValue(state['body_tracking']['body_contrast'])
        self.body_min_size_mm.setValue(state['body_tracking']['min_body_size_mm'])
        self.body_max_size_mm.setValue(state['body_tracking']['max_body_size_mm'])
        self.body_min_length_mm.setValue(state['body_tracking']['min_body_length_mm'])
        self.body_max_length_mm.setValue(state['body_tracking']['max_body_length_mm'])
        self.body_min_width_mm.setValue(state['body_tracking']['min_body_width_mm'])
        self.body_max_width_mm.setValue(state['body_tracking']['max_body_width_mm'])
        self.body_crop_width_mm.setValue(state['body_tracking']['crop_dimension_mm'][0])
        self.body_crop_height_mm.setValue(state['body_tracking']['crop_dimension_mm'][1])
        self.body_blur_sz_mm.setValue(state['body_tracking']['blur_sz_mm'])
        self.body_median_filter_sz_mm.setValue(state['body_tracking']['median_filter_sz_mm'])

        self.group_eyes.setChecked(state['eyes_tracking_enabled'])
        self.eyes_pix_per_mm.setValue(state['eyes_tracking']['pix_per_mm'])
        self.eyes_target_pix_per_mm.setValue(state['eyes_tracking']['target_pix_per_mm'])
        self.eyes_intensity_lo.setValue(state['eyes_tracking']['eye_thresh_lo'])
        self.eyes_intensity_hi.setValue(state['eyes_tracking']['eye_thresh_hi'])
        self.eyes_thresh_resolution.setValue(state['eyes_tracking']['eye_dyntresh_res'])
        self.eyes_brightness.setValue(state['eyes_tracking']['eye_brightness'])
        self.eyes_gamma.setValue(state['eyes_tracking']['eye_gamma'])
        self.eyes_contrast.setValue(state['eyes_tracking']['eye_contrast'])
        self.eyes_min_size_mm.setValue(state['eyes_tracking']['eye_size_lo_mm'])
        self.eyes_max_size_mm.setValue(state['eyes_tracking']['eye_size_hi_mm'])
        self.eyes_offset_mm.setValue(state['eyes_tracking']['crop_offset_mm'])
        self.eyes_crop_width_mm.setValue(state['eyes_tracking']['crop_dimension_mm'][0])
        self.eyes_crop_height_mm.setValue(state['eyes_tracking']['crop_dimension_mm'][1])
        self.eyes_blur_sz_mm.setValue(state['eyes_tracking']['blur_sz_mm'])
        self.eyes_median_filter_sz_mm.setValue(state['eyes_tracking']['median_filter_sz_mm'])

        self.group_tail.setChecked(state['tail_tracking_enabled'])
        self.tail_pix_per_mm.setValue(state['tail_tracking']['pix_per_mm'])
        self.tail_target_pix_per_mm.setValue(state['tail_tracking']['target_pix_per_mm'])
        self.tail_brightness.setValue(state['tail_tracking']['tail_brightness'])
        self.tail_gamma.setValue(state['tail_tracking']['tail_gamma'])
        self.tail_contrast.setValue(state['tail_tracking']['tail_contrast'])
        self.tail_ball_radius_mm.setValue(state['tail_tracking']['ball_radius_mm'])
        self.tail_arc_angle_deg.setValue(state['tail_tracking']['arc_angle_deg'])
        self.tail_n_points_arc.setValue(state['tail_tracking']['n_pts_arc'])
        self.n_tail_points.setValue(state['tail_tracking']['n_tail_points'])
        self.n_tail_points_interp.setValue(state['tail_tracking']['n_pts_interp'])
        self.tail_length_mm.setValue(state['tail_tracking']['tail_length_mm'])
        self.swim_bladder_mm.setValue(state['tail_tracking']['dist_swim_bladder_mm'])
        self.tail_crop_width_mm.setValue(state['tail_tracking']['crop_dimension_mm'][0])
        self.tail_crop_height_mm.setValue(state['tail_tracking']['crop_dimension_mm'][1])
        self.tail_offset_mm.setValue(state['tail_tracking']['crop_offset_tail_mm'])
        self.tail_blur_sz_mm.setValue(state['tail_tracking']['blur_sz_mm'])
        self.tail_median_filter_sz_mm.setValue(state['tail_tracking']['median_filter_sz_mm'])

