from typing import Dict
from PyQt5.QtWidgets import (
    QWidget, 
    QApplication,
    QVBoxLayout, 
    QHBoxLayout, 
    QGroupBox,
    QFileDialog,
    QPushButton,
    QCheckBox
)
from PyQt5.QtCore import pyqtSignal
from qt_widgets import (
    LabeledDoubleSpinBox, 
    LabeledSpinBox, 
    LabeledComboBox
)
import json
from pathlib import Path

class Animal(QWidget):

    state_changed = pyqtSignal() 

    def __init__(
            self,
            pix_per_mm: float = 30,
            *args,
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.pix_per_mm = pix_per_mm
        self.declare_components()
        self.layout_components()

    def declare_components(self) -> None:

        self.animal_num_animals = LabeledSpinBox()
        self.animal_num_animals.setText('#animals')
        self.animal_num_animals.setRange(0,100)
        self.animal_num_animals.setSingleStep(1)
        self.animal_num_animals.setValue(1)
        self.animal_num_animals.valueChanged.connect(self.state_changed)
        self.animal_num_animals.setEnabled(False)
    
        self.animal_pix_per_mm = LabeledDoubleSpinBox()
        self.animal_pix_per_mm.setText('pix/mm')
        self.animal_pix_per_mm.setRange(1,200)
        self.animal_pix_per_mm.setValue(self.pix_per_mm)
        self.animal_pix_per_mm.setSingleStep(0.25)
        self.animal_pix_per_mm.valueChanged.connect(self.state_changed)

        self.animal_target_pix_per_mm = LabeledDoubleSpinBox()
        self.animal_target_pix_per_mm.setText('target pix/mm')
        self.animal_target_pix_per_mm.setRange(1,200)
        self.animal_target_pix_per_mm.setValue(5)
        self.animal_target_pix_per_mm.setSingleStep(0.25)
        self.animal_target_pix_per_mm.valueChanged.connect(self.state_changed)

        self.animal_intensity = LabeledDoubleSpinBox()
        self.animal_intensity.setText('intensity')
        self.animal_intensity.setRange(0,1)
        self.animal_intensity.setSingleStep(0.025)
        self.animal_intensity.setValue(0.15)
        self.animal_intensity.valueChanged.connect(self.state_changed)

        self.animal_gamma = LabeledDoubleSpinBox()
        self.animal_gamma.setText('gamma')
        self.animal_gamma.setRange(0.05,10)
        self.animal_gamma.setSingleStep(0.05)
        self.animal_gamma.setValue(1.0)
        self.animal_gamma.valueChanged.connect(self.state_changed)
        
        self.animal_contrast = LabeledDoubleSpinBox()
        self.animal_contrast.setText('contrast')
        self.animal_contrast.setRange(-10,10)
        self.animal_contrast.setSingleStep(0.05)
        self.animal_contrast.setValue(1.0)
        self.animal_contrast.valueChanged.connect(self.state_changed)

        self.animal_min_size_mm = LabeledDoubleSpinBox()
        self.animal_min_size_mm.setText('min area (mm2)')
        self.animal_min_size_mm.setRange(0,100_000)
        self.animal_min_size_mm.setSingleStep(1.0)
        self.animal_min_size_mm.setValue(0.0)
        self.animal_min_size_mm.valueChanged.connect(self.state_changed)

        self.animal_max_size_mm = LabeledDoubleSpinBox()
        self.animal_max_size_mm.setText('max area (mm2)')
        self.animal_max_size_mm.setRange(0,100_000)
        self.animal_max_size_mm.setSingleStep(1.0)
        self.animal_max_size_mm.setValue(300.0)
        self.animal_max_size_mm.valueChanged.connect(self.state_changed)

        self.animal_min_length_mm = LabeledDoubleSpinBox()
        self.animal_min_length_mm.setText('min length (mm)')
        self.animal_min_length_mm.setRange(0,100_000)
        self.animal_min_length_mm.setSingleStep(1.0)
        self.animal_min_length_mm.setValue(0.0)
        self.animal_min_length_mm.valueChanged.connect(self.state_changed)

        self.animal_max_length_mm = LabeledDoubleSpinBox()
        self.animal_max_length_mm.setText('max length (mm)')
        self.animal_max_length_mm.setRange(0,100_000)
        self.animal_max_length_mm.setSingleStep(1.0)
        self.animal_max_length_mm.setValue(0.0)
        self.animal_max_length_mm.valueChanged.connect(self.state_changed)

        self.animal_min_width_mm = LabeledDoubleSpinBox()
        self.animal_min_width_mm.setText('min width (mm)')
        self.animal_min_width_mm.setRange(0,100_000)
        self.animal_min_width_mm.setSingleStep(1.0)
        self.animal_min_width_mm.setValue(0.0)
        self.animal_min_width_mm.valueChanged.connect(self.state_changed)

        self.animal_max_width_mm = LabeledDoubleSpinBox()
        self.animal_max_width_mm.setText('max width (mm)')
        self.animal_max_width_mm.setRange(0,100_000)
        self.animal_max_width_mm.setSingleStep(1.0)
        self.animal_max_width_mm.setValue(0.0)
        self.animal_max_width_mm.valueChanged.connect(self.state_changed)

        self.animal_crop_offset_y_mm = LabeledDoubleSpinBox()
        self.animal_crop_offset_y_mm.setText('vertical offset (mm)')
        self.animal_crop_offset_y_mm.setRange(-10,10)
        self.animal_crop_offset_y_mm.setSingleStep(0.025)
        self.animal_crop_offset_y_mm.setValue(0.0)
        self.animal_crop_offset_y_mm.valueChanged.connect(self.state_changed)

        self.animal_crop_width_mm = LabeledDoubleSpinBox()
        self.animal_crop_width_mm.setText('crop width (mm)')
        self.animal_crop_width_mm.setRange(0,100)
        self.animal_crop_width_mm.setSingleStep(0.05)
        self.animal_crop_width_mm.setValue(0)
        self.animal_crop_width_mm.valueChanged.connect(self.state_changed)

        self.animal_crop_height_mm = LabeledDoubleSpinBox()
        self.animal_crop_height_mm.setText('crop height (mm)')
        self.animal_crop_height_mm.setRange(0,1000)
        self.animal_crop_height_mm.setSingleStep(0.05)
        self.animal_crop_height_mm.setValue(0)
        self.animal_crop_height_mm.valueChanged.connect(self.state_changed)

        self.animal_blur_sz_mm = LabeledDoubleSpinBox()
        self.animal_blur_sz_mm.setText('blur size (mm)')
        self.animal_blur_sz_mm.setRange(0,1000)
        self.animal_blur_sz_mm.setSingleStep(0.1)
        self.animal_blur_sz_mm.setValue(0.60)
        self.animal_blur_sz_mm.valueChanged.connect(self.state_changed)
        
        self.animal_median_filter_sz_mm = LabeledDoubleSpinBox()
        self.animal_median_filter_sz_mm.setText('medfilt size (mm)')
        self.animal_median_filter_sz_mm.setRange(0,1000)
        self.animal_median_filter_sz_mm.setSingleStep(0.1)
        self.animal_median_filter_sz_mm.setValue(0.0)
        self.animal_median_filter_sz_mm.valueChanged.connect(self.state_changed)

        self.animal_downsample_factor = LabeledDoubleSpinBox()
        self.animal_downsample_factor.setText('downsample ratio')
        self.animal_downsample_factor.setRange(0.1,1.0)
        self.animal_downsample_factor.setSingleStep(0.05)
        self.animal_downsample_factor.setValue(0.25)
        self.animal_downsample_factor.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:

        animal = QVBoxLayout(self)
        animal.addWidget(self.animal_num_animals)
        animal.addWidget(self.animal_pix_per_mm)
        animal.addWidget(self.animal_target_pix_per_mm)
        animal.addWidget(self.animal_intensity)
        animal.addWidget(self.animal_gamma)
        animal.addWidget(self.animal_contrast)
        animal.addWidget(self.animal_min_size_mm)
        animal.addWidget(self.animal_max_size_mm)
        animal.addWidget(self.animal_min_length_mm)
        animal.addWidget(self.animal_max_length_mm)
        animal.addWidget(self.animal_min_width_mm)
        animal.addWidget(self.animal_max_width_mm)
        animal.addWidget(self.animal_crop_offset_y_mm)
        animal.addWidget(self.animal_crop_width_mm)
        animal.addWidget(self.animal_crop_height_mm)
        animal.addWidget(self.animal_blur_sz_mm)
        animal.addWidget(self.animal_median_filter_sz_mm)
        animal.addWidget(self.animal_downsample_factor)
        animal.addStretch()

    def get_state(self) -> Dict:
        
        state = {}
        state['pix_per_mm'] = self.animal_pix_per_mm.value()
        state['target_pix_per_mm'] = self.animal_target_pix_per_mm.value()
        state['intensity'] = self.animal_intensity.value()
        state['gamma'] = self.animal_gamma.value()
        state['contrast'] = self.animal_contrast.value()
        state['min_size_mm'] = self.animal_min_size_mm.value()
        state['max_size_mm'] = self.animal_max_size_mm.value()
        state['min_length_mm'] = self.animal_min_length_mm.value()
        state['max_length_mm'] = self.animal_max_length_mm.value()
        state['min_width_mm'] = self.animal_min_width_mm.value()
        state['max_width_mm'] = self.animal_max_width_mm.value()
        state['blur_sz_mm'] = self.animal_blur_sz_mm.value()
        state['median_filter_sz_mm'] = self.animal_median_filter_sz_mm.value()
        state['downsample_factor'] = self.animal_downsample_factor.value()
        state['crop_offset_y_mm'] = self.animal_crop_offset_y_mm.value()
        state['crop_dimension_mm'] = (self.animal_crop_width_mm.value(),self.animal_crop_height_mm.value())
        state['num_animals'] = self.animal_num_animals.value()

        return state
    
    def set_state(self, state: Dict) -> None:

        setters = {
            'target_pix_per_mm': self.animal_target_pix_per_mm.setValue,
            'intensity': self.animal_intensity.setValue,
            'gamma': self.animal_gamma.setValue,
            'contrast': self.animal_contrast.setValue,
            'min_size_mm': self.animal_min_size_mm.setValue,
            'max_size_mm': self.animal_max_size_mm.setValue,
            'min_length_mm': self.animal_min_length_mm.setValue,
            'max_length_mm': self.animal_max_length_mm.setValue,
            'min_width_mm': self.animal_min_width_mm.setValue,
            'max_width_mm': self.animal_max_width_mm.setValue,
            'crop_offset_y_mm': self.animal_crop_offset_y_mm.setValue,
            'crop_dimension_mm': lambda x: (
                self.animal_crop_width_mm.setValue(x[0]),
                self.animal_crop_height_mm.setValue(x[1]),
            ),
            'blur_sz_mm': self.animal_blur_sz_mm.setValue,
            'median_filter_sz_mm': self.animal_median_filter_sz_mm.setValue,
            'num_animals': self.animal_num_animals.setValue,
            'downsample_ratio': self.animal_downsample_factor.setValue
        }
        
        for key, setter in setters.items():
            if key in state:
                setter(state[key])

class Body(QWidget):

    state_changed = pyqtSignal()

    def __init__(
            self,
            pix_per_mm: float = 30,
            *args,
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.pix_per_mm = pix_per_mm
        self.declare_components()
        self.layout_components()

    def declare_components(self) -> None:

        self.body_pix_per_mm = LabeledDoubleSpinBox()
        self.body_pix_per_mm.setText('pix/mm')
        self.body_pix_per_mm.setRange(1,200)
        self.body_pix_per_mm.setSingleStep(0.25)
        self.body_pix_per_mm.setValue(self.pix_per_mm)
        self.body_pix_per_mm.valueChanged.connect(self.state_changed)
        
        self.body_target_pix_per_mm = LabeledDoubleSpinBox()
        self.body_target_pix_per_mm.setText('target pix/mm')
        self.body_target_pix_per_mm.setRange(1,200)
        self.body_target_pix_per_mm.setSingleStep(0.25)
        self.body_target_pix_per_mm.setValue(7.5)
        self.body_target_pix_per_mm.valueChanged.connect(self.state_changed)
        
        self.body_intensity = LabeledDoubleSpinBox()
        self.body_intensity.setText('intensity')
        self.body_intensity.setRange(0,1)
        self.body_intensity.setSingleStep(0.025)
        self.body_intensity.setValue(0.15)
        self.body_intensity.valueChanged.connect(self.state_changed)

        self.body_gamma = LabeledDoubleSpinBox()
        self.body_gamma.setText('gamma')
        self.body_gamma.setRange(0.05,10)
        self.body_gamma.setSingleStep(0.05)
        self.body_gamma.setValue(1.0)
        self.body_gamma.valueChanged.connect(self.state_changed)

        self.body_contrast = LabeledDoubleSpinBox()
        self.body_contrast.setText('contrast')
        self.body_contrast.setRange(-10,10)
        self.body_contrast.setSingleStep(0.05)
        self.body_contrast.setValue(1.0)
        self.body_contrast.valueChanged.connect(self.state_changed)

        self.body_min_size_mm = LabeledDoubleSpinBox()
        self.body_min_size_mm.setText('min area (mm2)')
        self.body_min_size_mm.setRange(0,100_000)
        self.body_min_size_mm.setSingleStep(1.0)
        self.body_min_size_mm.setValue(0.0)
        self.body_min_size_mm.valueChanged.connect(self.state_changed)

        self.body_max_size_mm = LabeledDoubleSpinBox()
        self.body_max_size_mm.setText('max area (mm2)')
        self.body_max_size_mm.setRange(0,100_000)
        self.body_max_size_mm.setSingleStep(1.0)
        self.body_max_size_mm.setValue(300)
        self.body_max_size_mm.valueChanged.connect(self.state_changed)

        self.body_min_length_mm = LabeledDoubleSpinBox()
        self.body_min_length_mm.setText('min length (mm)')
        self.body_min_length_mm.setRange(0,100_000)
        self.body_min_length_mm.setSingleStep(1.0)
        self.body_min_length_mm.setValue(0.0)
        self.body_min_length_mm.valueChanged.connect(self.state_changed)

        self.body_max_length_mm = LabeledDoubleSpinBox()
        self.body_max_length_mm.setText('max length (mm)')
        self.body_max_length_mm.setRange(0,100_000)
        self.body_max_length_mm.setSingleStep(1.0)
        self.body_max_length_mm.setValue(0.0)
        self.body_max_length_mm.valueChanged.connect(self.state_changed)

        self.body_min_width_mm = LabeledDoubleSpinBox()
        self.body_min_width_mm.setText('min width (mm)')
        self.body_min_width_mm.setRange(0,100_000)
        self.body_min_width_mm.setSingleStep(1.0)
        self.body_min_width_mm.setValue(0.0)
        self.body_min_width_mm.valueChanged.connect(self.state_changed)

        self.body_max_width_mm = LabeledDoubleSpinBox()
        self.body_max_width_mm.setText('max width (mm)')
        self.body_max_width_mm.setRange(0,100_000)
        self.body_max_width_mm.setSingleStep(1.0)
        self.body_max_width_mm.setValue(0.0)
        self.body_max_width_mm.valueChanged.connect(self.state_changed)

        self.body_crop_offset_y_mm = LabeledDoubleSpinBox()
        self.body_crop_offset_y_mm.setText('vertical offset (mm)')
        self.body_crop_offset_y_mm.setRange(-10,10)
        self.body_crop_offset_y_mm.setSingleStep(0.025)
        self.body_crop_offset_y_mm.setValue(0.0)
        self.body_crop_offset_y_mm.valueChanged.connect(self.state_changed)

        self.body_crop_width_mm = LabeledDoubleSpinBox()
        self.body_crop_width_mm.setText('crop width (mm)')
        self.body_crop_width_mm.setRange(0,1000)
        self.body_crop_width_mm.setSingleStep(0.05)
        self.body_crop_width_mm.setValue(9)
        self.body_crop_width_mm.valueChanged.connect(self.state_changed)

        self.body_crop_height_mm = LabeledDoubleSpinBox()
        self.body_crop_height_mm.setText('crop height (mm)')
        self.body_crop_height_mm.setRange(0,1000)
        self.body_crop_height_mm.setSingleStep(0.05)
        self.body_crop_height_mm.setValue(9)
        self.body_crop_height_mm.valueChanged.connect(self.state_changed)

        self.body_blur_sz_mm = LabeledDoubleSpinBox()
        self.body_blur_sz_mm.setText('blur size (mm)')
        self.body_blur_sz_mm.setRange(0,1000)
        self.body_blur_sz_mm.setSingleStep(0.1)
        self.body_blur_sz_mm.setValue(0.60)
        self.body_blur_sz_mm.valueChanged.connect(self.state_changed)

        self.body_median_filter_sz_mm = LabeledDoubleSpinBox()
        self.body_median_filter_sz_mm.setText('medfilt size (mm)')
        self.body_median_filter_sz_mm.setRange(0,1000)
        self.body_median_filter_sz_mm.setSingleStep(0.1)
        self.body_median_filter_sz_mm.setValue(0.0)
        self.body_median_filter_sz_mm.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:

        body = QVBoxLayout(self)
        body.addWidget(self.body_pix_per_mm)
        body.addWidget(self.body_target_pix_per_mm)
        body.addWidget(self.body_intensity)
        body.addWidget(self.body_gamma)
        body.addWidget(self.body_contrast)
        body.addWidget(self.body_min_size_mm)
        body.addWidget(self.body_max_size_mm)
        body.addWidget(self.body_min_length_mm)
        body.addWidget(self.body_max_length_mm)
        body.addWidget(self.body_min_width_mm)
        body.addWidget(self.body_max_width_mm)
        body.addWidget(self.body_crop_offset_y_mm)
        body.addWidget(self.body_crop_width_mm)
        body.addWidget(self.body_crop_height_mm)
        body.addWidget(self.body_blur_sz_mm)
        body.addWidget(self.body_median_filter_sz_mm)
        body.addStretch()

    def get_state(self) -> Dict:

        state = {}
        state['pix_per_mm'] = self.body_pix_per_mm.value()
        state['target_pix_per_mm']=self.body_target_pix_per_mm.value()
        state['intensity']=self.body_intensity.value()
        state['gamma']=self.body_gamma.value()
        state['contrast']=self.body_contrast.value()
        state['min_size_mm']=self.body_min_size_mm.value()
        state['max_size_mm']=self.body_max_size_mm.value()
        state['min_length_mm']=self.body_min_length_mm.value()
        state['max_length_mm']=self.body_max_length_mm.value()
        state['min_width_mm']=self.body_min_width_mm.value()
        state['max_width_mm']=self.body_max_width_mm.value()
        state['crop_offset_y_mm']=self.body_crop_offset_y_mm.value()
        state['crop_dimension_mm']=(self.body_crop_width_mm.value(),self.body_crop_height_mm.value())
        state['blur_sz_mm']=self.body_blur_sz_mm.value()
        state['median_filter_sz_mm']=self.body_median_filter_sz_mm.value()

        return state

    def set_state(self, state: Dict) -> None:

        setters = {
            'target_pix_per_mm': self.body_target_pix_per_mm.setValue,
            'intensity': self.body_intensity.setValue,
            'gamma': self.body_gamma.setValue,
            'contrast': self.body_contrast.setValue,
            'min_size_mm': self.body_min_size_mm.setValue,
            'max_size_mm': self.body_max_size_mm.setValue,
            'min_length_mm': self.body_min_length_mm.setValue,
            'max_length_mm': self.body_max_length_mm.setValue,
            'min_width_mm': self.body_min_width_mm.setValue,
            'max_width_mm': self.body_max_width_mm.setValue,
            'crop_offset_y_mm': self.body_crop_offset_y_mm.setValue,
            'crop_dimension_mm': lambda x: (
                self.body_crop_width_mm.setValue(x[0]),
                self.body_crop_height_mm.setValue(x[1])
            ),
            'blur_sz_mm': self.body_blur_sz_mm.setValue,
            'median_filter_sz_mm': self.body_median_filter_sz_mm.setValue
        }

        for key, setter in setters.items():
            if key in state:
                setter(state[key])

class Eyes(QWidget):

    state_changed = pyqtSignal()
    
    def __init__(
            self,
            pix_per_mm: float = 30,
            *args,
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.pix_per_mm = pix_per_mm
        self.declare_components()
        self.layout_components()

    def declare_components(self) -> None:

        self.eyes_pix_per_mm = LabeledDoubleSpinBox()
        self.eyes_pix_per_mm.setText('pix/mm')
        self.eyes_pix_per_mm.setRange(1,200)
        self.eyes_pix_per_mm.setSingleStep(0.25)
        self.eyes_pix_per_mm.setValue(self.pix_per_mm)
        self.eyes_pix_per_mm.valueChanged.connect(self.state_changed)

        self.eyes_target_pix_per_mm = LabeledDoubleSpinBox()
        self.eyes_target_pix_per_mm.setText('target pix/mm')
        self.eyes_target_pix_per_mm.setRange(1,200)
        self.eyes_target_pix_per_mm.setSingleStep(0.25)
        self.eyes_target_pix_per_mm.setValue(30)
        self.eyes_target_pix_per_mm.valueChanged.connect(self.state_changed)
        
        self.eyes_intensity_lo = LabeledDoubleSpinBox()
        self.eyes_intensity_lo.setText('thresh low')
        self.eyes_intensity_lo.setRange(0,1)
        self.eyes_intensity_lo.setSingleStep(0.025)
        self.eyes_intensity_lo.setValue(0.2)
        self.eyes_intensity_lo.valueChanged.connect(self.state_changed)

        self.eyes_intensity_hi = LabeledDoubleSpinBox()
        self.eyes_intensity_hi.setText('thresh high')
        self.eyes_intensity_hi.setRange(0,1)
        self.eyes_intensity_hi.setSingleStep(0.025)
        self.eyes_intensity_hi.setValue(1.0)
        self.eyes_intensity_hi.valueChanged.connect(self.state_changed)

        self.eyes_thresh_resolution = LabeledSpinBox()
        self.eyes_thresh_resolution.setText('thresh steps')
        self.eyes_thresh_resolution.setSingleStep(1)
        self.eyes_thresh_resolution.setRange(1,100)
        self.eyes_thresh_resolution.setValue(5)
        self.eyes_thresh_resolution.valueChanged.connect(self.state_changed)

        self.eyes_gamma = LabeledDoubleSpinBox()
        self.eyes_gamma.setText('gamma')
        self.eyes_gamma.setRange(0.05,10)
        self.eyes_gamma.setSingleStep(0.05)
        self.eyes_gamma.setValue(1.0)
        self.eyes_gamma.valueChanged.connect(self.state_changed)

        self.eyes_contrast = LabeledDoubleSpinBox()
        self.eyes_contrast.setText('contrast')
        self.eyes_contrast.setRange(-10,10)
        self.eyes_contrast.setSingleStep(0.05)
        self.eyes_contrast.setValue(1.0)
        self.eyes_contrast.valueChanged.connect(self.state_changed)

        self.eyes_min_size_mm = LabeledDoubleSpinBox()
        self.eyes_min_size_mm.setText('min area (mm2)')
        self.eyes_min_size_mm.setRange(0,1000)
        self.eyes_min_size_mm.setSingleStep(1.0)
        self.eyes_min_size_mm.setValue(0.0)
        self.eyes_min_size_mm.valueChanged.connect(self.state_changed)

        self.eyes_max_size_mm = LabeledDoubleSpinBox()
        self.eyes_max_size_mm.setText('max area (mm2)')
        self.eyes_max_size_mm.setRange(0,1000)
        self.eyes_max_size_mm.setSingleStep(1.0)
        self.eyes_max_size_mm.setValue(30.0)
        self.eyes_max_size_mm.valueChanged.connect(self.state_changed)

        self.eyes_crop_offset_y_mm = LabeledDoubleSpinBox()
        self.eyes_crop_offset_y_mm.setText('vertical offset (mm)')
        self.eyes_crop_offset_y_mm.setRange(-10,10)
        self.eyes_crop_offset_y_mm.setSingleStep(0.025)
        self.eyes_crop_offset_y_mm.setValue(-0.25)
        self.eyes_crop_offset_y_mm.valueChanged.connect(self.state_changed)

        self.eyes_crop_width_mm = LabeledDoubleSpinBox()
        self.eyes_crop_width_mm.setText('crop width (mm)')
        self.eyes_crop_width_mm.setRange(0,1000)
        self.eyes_crop_width_mm.setSingleStep(0.05)
        self.eyes_crop_width_mm.setValue(1)
        self.eyes_crop_width_mm.valueChanged.connect(self.state_changed)

        self.eyes_crop_height_mm = LabeledDoubleSpinBox()
        self.eyes_crop_height_mm.setText('crop height (mm)')
        self.eyes_crop_height_mm.setRange(0,1000)
        self.eyes_crop_height_mm.setSingleStep(0.05)
        self.eyes_crop_height_mm.setValue(1.5)
        self.eyes_crop_height_mm.valueChanged.connect(self.state_changed)

        self.eyes_blur_sz_mm = LabeledDoubleSpinBox()
        self.eyes_blur_sz_mm.setText('blur size (mm)')
        self.eyes_blur_sz_mm.setRange(0,1000)
        self.eyes_blur_sz_mm.setSingleStep(0.1)
        self.eyes_blur_sz_mm.setValue(0.1)
        self.eyes_blur_sz_mm.valueChanged.connect(self.state_changed)

        self.eyes_median_filter_sz_mm = LabeledDoubleSpinBox()
        self.eyes_median_filter_sz_mm.setText('medfilt size (mm)')
        self.eyes_median_filter_sz_mm.setRange(0,1000)
        self.eyes_median_filter_sz_mm.setSingleStep(0.1)
        self.eyes_median_filter_sz_mm.setValue(0.0)
        self.eyes_median_filter_sz_mm.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:

        eyes = QVBoxLayout(self)
        eyes.addWidget(self.eyes_pix_per_mm)
        eyes.addWidget(self.eyes_target_pix_per_mm)
        eyes.addWidget(self.eyes_intensity_lo)
        eyes.addWidget(self.eyes_intensity_hi)
        eyes.addWidget(self.eyes_thresh_resolution)
        eyes.addWidget(self.eyes_gamma)
        eyes.addWidget(self.eyes_contrast)
        eyes.addWidget(self.eyes_min_size_mm)
        eyes.addWidget(self.eyes_max_size_mm)
        eyes.addWidget(self.eyes_crop_offset_y_mm)
        eyes.addWidget(self.eyes_crop_width_mm)
        eyes.addWidget(self.eyes_crop_height_mm)
        eyes.addWidget(self.eyes_blur_sz_mm)
        eyes.addWidget(self.eyes_median_filter_sz_mm)
        eyes.addStretch()

    def get_state(self) -> Dict:

        state = {}
        state['pix_per_mm'] = self.eyes_pix_per_mm.value()
        state['target_pix_per_mm']=self.eyes_target_pix_per_mm.value()
        state['thresh_lo']=self.eyes_intensity_lo.value()
        state['thresh_hi']=self.eyes_intensity_hi.value()
        state['dyntresh_res']=self.eyes_thresh_resolution.value()
        state['gamma']=self.eyes_gamma.value()
        state['contrast']=self.eyes_contrast.value()
        state['size_lo_mm']=self.eyes_min_size_mm.value()
        state['size_hi_mm']=self.eyes_max_size_mm.value()
        state['crop_offset_y_mm']=self.eyes_crop_offset_y_mm.value()
        state['crop_dimension_mm']=(self.eyes_crop_width_mm.value(),self.eyes_crop_height_mm.value())
        state['blur_sz_mm']=self.eyes_blur_sz_mm.value()
        state['median_filter_sz_mm']=self.eyes_median_filter_sz_mm.value()

        return state
    
    def set_state(self, state: Dict) -> None:

        setters = {
            'target_pix_per_mm': self.eyes_target_pix_per_mm.setValue,
            'thresh_lo': self.eyes_intensity_lo.setValue,
            'thresh_hi': self.eyes_intensity_hi.setValue,
            'dyntresh_res': self.eyes_thresh_resolution.setValue,
            'gamma': self.eyes_gamma.setValue,
            'contrast': self.eyes_contrast.setValue,
            'size_lo_mm': self.eyes_min_size_mm.setValue,
            'size_hi_mm': self.eyes_max_size_mm.setValue,
            'crop_offset_y_mm': self.eyes_crop_offset_y_mm.setValue,
            'crop_dimension_mm': lambda x: (
                self.eyes_crop_width_mm.setValue(x[0]),
                self.eyes_crop_height_mm.setValue(x[1])
            ),
            'blur_sz_mm': self.eyes_blur_sz_mm.setValue,
            'median_filter_sz_mm': self.eyes_median_filter_sz_mm.setValue
        }

        for key, setter in setters.items():
            if key in state:
                setter(state[key])

class Tail(QWidget):
    
    state_changed = pyqtSignal()

    def __init__(
            self,
            pix_per_mm: float = 30,
            *args,
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.pix_per_mm = pix_per_mm
        self.declare_components()
        self.layout_components()

    def declare_components(self) -> None:

        self.tail_pix_per_mm = LabeledDoubleSpinBox()
        self.tail_pix_per_mm.setText('pix/mm')
        self.tail_pix_per_mm.setRange(1,200)
        self.tail_pix_per_mm.setSingleStep(0.25)
        self.tail_pix_per_mm.setValue(self.pix_per_mm)
        self.tail_pix_per_mm.valueChanged.connect(self.state_changed)
        
        self.tail_target_pix_per_mm = LabeledDoubleSpinBox()
        self.tail_target_pix_per_mm.setText('target pix/mm')
        self.tail_target_pix_per_mm.setRange(1,200)
        self.tail_target_pix_per_mm.setSingleStep(0.25)
        self.tail_target_pix_per_mm.setValue(20)
        self.tail_target_pix_per_mm.valueChanged.connect(self.state_changed)

        self.tail_gamma = LabeledDoubleSpinBox()
        self.tail_gamma.setText('gamma')
        self.tail_gamma.setRange(0.05,10)
        self.tail_gamma.setSingleStep(0.05)
        self.tail_gamma.setValue(1.0)
        self.tail_gamma.valueChanged.connect(self.state_changed)

        self.tail_contrast = LabeledDoubleSpinBox()
        self.tail_contrast.setText('contrast')
        self.tail_contrast.setRange(-10,10)
        self.tail_contrast.setSingleStep(0.05)
        self.tail_contrast.setValue(1.0)
        self.tail_contrast.valueChanged.connect(self.state_changed)

        self.tail_ball_radius_mm = LabeledDoubleSpinBox()
        self.tail_ball_radius_mm.setText('ball radius (mm)')
        self.tail_ball_radius_mm.setRange(0.05,10)
        self.tail_ball_radius_mm.setSingleStep(0.01)
        self.tail_ball_radius_mm.setValue(0.15)
        self.tail_ball_radius_mm.valueChanged.connect(self.state_changed)

        self.tail_arc_angle_deg = LabeledDoubleSpinBox()
        self.tail_arc_angle_deg.setText('arc angle (deg)')
        self.tail_arc_angle_deg.setRange(1,360)
        self.tail_arc_angle_deg.setSingleStep(1.0)
        self.tail_arc_angle_deg.setValue(90)
        self.tail_arc_angle_deg.valueChanged.connect(self.state_changed)
        
        self.tail_n_points_arc = LabeledSpinBox()
        self.tail_n_points_arc.setText('arc resolution')
        self.tail_n_points_arc.setRange(2,100)
        self.tail_n_points_arc.setSingleStep(1)
        self.tail_n_points_arc.setValue(20)
        self.tail_n_points_arc.valueChanged.connect(self.state_changed)

        self.n_tail_points = LabeledSpinBox()
        self.n_tail_points.setText('#tail points')
        self.n_tail_points.setRange(3,100)
        self.n_tail_points.setSingleStep(1)
        self.n_tail_points.setValue(6)
        self.n_tail_points.valueChanged.connect(self.state_changed)

        self.n_tail_points_interp = LabeledSpinBox()
        self.n_tail_points_interp.setText('#tail points interp')
        self.n_tail_points_interp.setRange(2,100)
        self.n_tail_points_interp.setSingleStep(1)
        self.n_tail_points_interp.setValue(40)
        self.n_tail_points_interp.valueChanged.connect(self.state_changed)
        self.n_tail_points_interp.setEnabled(False) # This cant change because it would change columns in output csv 

        self.tail_length_mm = LabeledDoubleSpinBox()
        self.tail_length_mm.setText('tail length (mm)')
        self.tail_length_mm.setRange(0.5,10)
        self.tail_length_mm.setSingleStep(0.05)
        self.tail_length_mm.setValue(3.75)
        self.tail_length_mm.valueChanged.connect(self.state_changed)

        self.tail_crop_offset_y_mm = LabeledDoubleSpinBox()
        self.tail_crop_offset_y_mm.setText('vertical offset (mm)')
        self.tail_crop_offset_y_mm.setRange(0,10)
        self.tail_crop_offset_y_mm.setSingleStep(0.025)
        self.tail_crop_offset_y_mm.setValue(2.75)
        self.tail_crop_offset_y_mm.valueChanged.connect(self.state_changed)

        self.tail_crop_width_mm = LabeledDoubleSpinBox()
        self.tail_crop_width_mm.setText('crop width (mm)')
        self.tail_crop_width_mm.setRange(0,1000)
        self.tail_crop_width_mm.setSingleStep(0.05)
        self.tail_crop_width_mm.setValue(4)
        self.tail_crop_width_mm.valueChanged.connect(self.state_changed)

        self.tail_crop_height_mm = LabeledDoubleSpinBox()
        self.tail_crop_height_mm.setText('crop height (mm)')
        self.tail_crop_height_mm.setRange(0,1000)
        self.tail_crop_height_mm.setSingleStep(0.05)
        self.tail_crop_height_mm.setValue(4)
        self.tail_crop_height_mm.valueChanged.connect(self.state_changed)

        self.tail_blur_sz_mm = LabeledDoubleSpinBox()
        self.tail_blur_sz_mm.setText('blur size (mm)')
        self.tail_blur_sz_mm.setRange(0,1000)
        self.tail_blur_sz_mm.setSingleStep(0.1)
        self.tail_blur_sz_mm.setValue(0.1)
        self.tail_blur_sz_mm.valueChanged.connect(self.state_changed)

        self.tail_median_filter_sz_mm = LabeledDoubleSpinBox()
        self.tail_median_filter_sz_mm.setText('medfilt size (mm)')
        self.tail_median_filter_sz_mm.setRange(0,1000)
        self.tail_median_filter_sz_mm.setSingleStep(0.1)
        self.tail_median_filter_sz_mm.setValue(0.1)
        self.tail_median_filter_sz_mm.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:

        tail = QVBoxLayout(self)
        tail.addWidget(self.tail_pix_per_mm)
        tail.addWidget(self.tail_target_pix_per_mm)
        tail.addWidget(self.tail_gamma)
        tail.addWidget(self.tail_contrast)
        tail.addWidget(self.tail_ball_radius_mm)
        tail.addWidget(self.tail_arc_angle_deg)
        tail.addWidget(self.tail_n_points_arc)
        tail.addWidget(self.n_tail_points)
        tail.addWidget(self.n_tail_points_interp)
        tail.addWidget(self.tail_length_mm)
        tail.addWidget(self.tail_crop_offset_y_mm)
        tail.addWidget(self.tail_crop_width_mm)
        tail.addWidget(self.tail_crop_height_mm)
        tail.addWidget(self.tail_blur_sz_mm)
        tail.addWidget(self.tail_median_filter_sz_mm)
        tail.addStretch()

    def get_state(self) -> Dict:

        state = {}
        state['pix_per_mm'] = self.tail_pix_per_mm.value()
        state['target_pix_per_mm']=self.tail_target_pix_per_mm.value()
        state['gamma']=self.tail_gamma.value()
        state['contrast']=self.tail_contrast.value()
        state['ball_radius_mm']=self.tail_ball_radius_mm.value()
        state['arc_angle_deg']=self.tail_arc_angle_deg.value()
        state['n_pts_arc']=self.tail_n_points_arc.value()
        state['n_tail_points']=self.n_tail_points.value()
        state['n_pts_interp']=self.n_tail_points_interp.value()
        state['tail_length_mm']=self.tail_length_mm.value()
        state['crop_dimension_mm']=(self.tail_crop_width_mm.value(),self.tail_crop_height_mm.value())
        state['crop_offset_y_mm']=self.tail_crop_offset_y_mm.value()
        state['blur_sz_mm']=self.tail_blur_sz_mm.value()
        state['median_filter_sz_mm']=self.tail_median_filter_sz_mm.value()

        return state
    
    def set_state(self, state: Dict) -> None:
        
        setters = {
            'target_pix_per_mm': self.tail_target_pix_per_mm.setValue,
            'gamma': self.tail_gamma.setValue,
            'contrast': self.tail_contrast.setValue,
            'ball_radius_mm': self.tail_ball_radius_mm.setValue,
            'arc_angle_deg': self.tail_arc_angle_deg.setValue,
            'n_pts_arc': self.tail_n_points_arc.setValue,
            'n_tail_points': self.n_tail_points.setValue,
            'n_pts_interp': self.n_tail_points_interp.setValue,
            'tail_length_mm': self.tail_length_mm.setValue,
            'crop_offset_y_mm': self.tail_crop_offset_y_mm.setValue,
            'crop_dimension_mm': lambda x: (
                self.tail_crop_width_mm.setValue(x[0]),
                self.tail_crop_height_mm.setValue(x[1])    
            ),
            'blur_sz_mm': self.tail_blur_sz_mm.setValue,
            'median_filter_sz_mm': self.tail_median_filter_sz_mm.setValue
        }

        for key, setter in setters.items():
            if key in state:
                setter(state[key])

class TrackerWidget(QWidget):

    state_changed = pyqtSignal()

    def __init__(
            self,
            settings_file: Path = Path('tracking.json'),
            n_animals: int = 1,
            pix_per_mm: float = 30,
            *args,
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.updated = True
        self.settings_file = settings_file
        self.n_animals = n_animals
        self.pix_per_mm = pix_per_mm 
            
        self.declare_components()
        self.layout_components()
        self.setWindowTitle('Tracking controls')
        
        self.current_animal = 0
        self.substate = {}
        for i in range(self.n_animals):
            self.substate[i] = self._get_substate()

        if settings_file.exists():
            self.load_from_file(settings_file)

    def declare_components(self) -> None:

        self.assignment_choice = LabeledComboBox()
        self.assignment_choice.setText('Assignment:')
        self.assignment_choice.addItem('ROI')
        self.assignment_choice.addItem('Hungarian')
        self.assignment_choice.currentIndexChanged.connect(self.on_change)      
        self.assignment_choice.setEnabled(False)

        self.animal_identity = LabeledSpinBox()
        self.animal_identity.setText('#animal')
        self.animal_identity.setRange(0,self.n_animals-1)
        self.animal_identity.setSingleStep(1)
        self.animal_identity.setValue(0)
        self.animal_identity.valueChanged.connect(self.animal_changed)

        self.apply_to_all = QCheckBox('Apply to all animals')
        self.apply_to_all.setChecked(True)
        self.apply_to_all.stateChanged.connect(self.apply_to_all_changed)

        self.animal = Animal(pix_per_mm=self.pix_per_mm)
        self.animal.state_changed.connect(self.on_change)

        self.body = Body(pix_per_mm=self.pix_per_mm)
        self.body.state_changed.connect(self.on_change)

        self.eyes = Eyes(pix_per_mm=self.pix_per_mm)
        self.eyes.state_changed.connect(self.on_change)

        self.tail = Tail(pix_per_mm=self.pix_per_mm)
        self.tail.state_changed.connect(self.on_change)

        self.btn_load = QPushButton('load')
        self.btn_load.clicked.connect(self.load)

        self.btn_save = QPushButton('save')
        self.btn_save.clicked.connect(self.save)

    def layout_components(self) -> None:

        identity = QHBoxLayout()
        identity.addWidget(self.apply_to_all)
        identity.addWidget(self.animal_identity)

        animal = QHBoxLayout()
        animal.addWidget(self.animal)
        self.group_animal = QGroupBox('animal')
        self.group_animal.setLayout(animal)

        body = QHBoxLayout()
        body.addWidget(self.body)
        self.group_body = QGroupBox('body')
        self.group_body.setCheckable(True)
        self.group_body.setChecked(True)
        self.group_body.toggled.connect(self.on_change)
        self.group_body.setLayout(body)

        eyes = QHBoxLayout()
        eyes.addWidget(self.eyes)
        self.group_eyes = QGroupBox('eyes')
        self.group_eyes.setCheckable(True)
        self.group_eyes.setChecked(True)
        self.group_eyes.toggled.connect(self.on_change)
        self.group_eyes.setLayout(eyes)

        tail = QHBoxLayout()
        tail.addWidget(self.tail)
        self.group_tail = QGroupBox('tail')
        self.group_tail.setCheckable(True)
        self.group_tail.setChecked(True)
        self.group_tail.toggled.connect(self.on_change)
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
        final.addLayout(identity)
        final.addWidget(self.assignment_choice)
        final.addLayout(groups)
        final.addLayout(io_layout)

    def apply_to_all_changed(self):

        if self.apply_to_all.isChecked():
            self.animal_identity.setEnabled(False)
            for i in range(self.n_animals):
                self.substate[i] = self._get_substate()
        else:
            self.animal_identity.setEnabled(True)
            
        self.updated = True
        self.state_changed.emit()

    def on_change(self):
        
        if not self.group_body.isChecked():
            self.group_eyes.setChecked(False)
            self.group_tail.setChecked(False)

        if self.apply_to_all.isChecked():
            for i in range(self.n_animals):
                self.substate[i] = self._get_substate()
        else:
            id = self.animal_identity.value()
            self.substate[id] = self._get_substate()

        self.updated = True
        self.state_changed.emit()

    def block_all_signals(self, block: bool):
        for child in self.findChildren(QWidget): 
            child.blockSignals(block)

    def animal_changed(self, next_animal: int):
        self.substate[self.current_animal] = self._get_substate()
        self.block_all_signals(True)
        self._set_substate(next_animal, self.substate[next_animal])
        self.block_all_signals(False)
        self.current_animal = next_animal
        self.state_changed.emit()
        
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
        self.state_changed.emit()
        
    def load_from_file(self, filename):

        with open(filename, 'r') as fp:
            state = json.load(fp)

        self.set_state(state)
        self.updated = True

    def _get_substate(self)-> Dict:

        state = {}
        state['assignment'] = self.assignment_choice.currentText()
        state['body_tracking_enabled'] = self.group_body.isChecked()
        state['eyes_tracking_enabled'] = self.group_eyes.isChecked()
        state['tail_tracking_enabled'] = self.group_tail.isChecked()
        state['animal_tracking'] = self.animal.get_state()
        state['body_tracking'] = self.body.get_state()
        state['eyes_tracking'] = self.eyes.get_state()
        state['tail_tracking'] = self.tail.get_state()
        return state

    def get_state(self) -> Dict:

        state = {}
        state['apply_to_all'] = self.apply_to_all.isChecked()
        state['animal_identity'] = self.animal_identity.value()
        state['substate'] = self.substate
        return state

    def _set_substate(self, id: int, substate: Dict) -> None:

        setters = {
            'assignment': self.assignment_choice.setCurrentText,
            'body_tracking_enabled': self.group_body.setChecked,
            'eyes_tracking_enabled': self.group_eyes.setChecked,
            'tail_tracking_enabled': self.group_tail.setChecked,
            'animal_tracking': self.animal.set_state,
            'body_tracking': self.body.set_state,
            'eyes_tracking': self.eyes.set_state,
            'tail_tracking': self.tail.set_state,
        }

        for key, setter in setters.items():
            if key in substate:
                setter(substate[key])

        self.substate[id] = substate
    
    def _apply_substate(self, substates: Dict):

        for key, substate in substates.items():
            self._set_substate(int(key), substate)

    def set_state(self, state: Dict) -> None:
        
        defaults = {
            'apply_to_all': False,
            'animal_identity': 0,
            'substate': {}
        }
        for key, value in defaults.items():
            state.setdefault(key, value)

        setters = {
            'apply_to_all': self.apply_to_all.setChecked,
            'animal_identity': self.animal_identity.setValue,
            'substate': self._apply_substate
        }
        for key, setter in setters.items():
            setter(state[key])

if __name__ == "__main__":

    app = QApplication([])
    main = TrackerWidget()
    main.show()
    app.exec_()
