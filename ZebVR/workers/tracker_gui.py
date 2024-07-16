from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from qt_widgets import LabeledDoubleSpinBox
from ZebVR.config import ANIMAL_TRACKING_PARAM, BODY_TRACKING_PARAM, N_TRACKER_WORKERS

class TrackerGui(WorkerNode):

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
        self.animal_pix_per_mm.setValue(ANIMAL_TRACKING_PARAM['pix_per_mm'])

        self.animal_target_pix_per_mm = LabeledDoubleSpinBox()
        self.animal_target_pix_per_mm.setText('target pix/mm')
        self.animal_target_pix_per_mm.setRange(0,200)
        self.animal_target_pix_per_mm.setValue(ANIMAL_TRACKING_PARAM['target_pix_per_mm'])

        self.animal_intensity = LabeledDoubleSpinBox()
        self.animal_intensity.setText('intensity')
        self.animal_intensity.setRange(0,1)
        self.animal_intensity.setValue(ANIMAL_TRACKING_PARAM['animal_intensity'])

        self.animal_brightness = LabeledDoubleSpinBox()
        self.animal_brightness.setText('brightness')
        self.animal_brightness.setRange(-1,1)
        self.animal_brightness.setValue(ANIMAL_TRACKING_PARAM['animal_brightness'])

        self.animal_gamma = LabeledDoubleSpinBox()
        self.animal_gamma.setText('gamma')
        self.animal_gamma.setRange(-10,10)
        self.animal_gamma.setValue(ANIMAL_TRACKING_PARAM['animal_gamma'])

        self.animal_contrast = LabeledDoubleSpinBox()
        self.animal_contrast.setText('contrast')
        self.animal_contrast.setRange(-10,10)
        self.animal_contrast.setValue(ANIMAL_TRACKING_PARAM['animal_contrast'])
        
        self.animal_min_size_mm = LabeledDoubleSpinBox()
        self.animal_min_size_mm.setText('min area (mm2)')
        self.animal_min_size_mm.setRange(0,100_000)
        self.animal_min_size_mm.setValue(ANIMAL_TRACKING_PARAM['min_animal_size_mm'])

        self.animal_max_size_mm = LabeledDoubleSpinBox()
        self.animal_max_size_mm.setText('max area (mm2)')
        self.animal_max_size_mm.setRange(0,100_000)
        self.animal_max_size_mm.setValue(ANIMAL_TRACKING_PARAM['max_animal_size_mm'])

        self.animal_min_length_mm = LabeledDoubleSpinBox()
        self.animal_min_length_mm.setText('min öength (mm)')
        self.animal_min_length_mm.setRange(0,100_000)
        self.animal_min_length_mm.setValue(ANIMAL_TRACKING_PARAM['min_animal_length_mm'])
        
        self.animal_max_length_mm = LabeledDoubleSpinBox()
        self.animal_max_length_mm.setText('max length (mm)')
        self.animal_max_length_mm.setRange(0,100_000)
        self.animal_max_length_mm.setValue(ANIMAL_TRACKING_PARAM['max_animal_length_mm'])

        self.animal_min_width_mm = LabeledDoubleSpinBox()
        self.animal_min_width_mm.setText('min width (mm)')
        self.animal_min_width_mm.setRange(0,100_000)
        self.animal_min_width_mm.setValue(ANIMAL_TRACKING_PARAM['min_animal_width_mm'])

        self.animal_max_width_mm = LabeledDoubleSpinBox()
        self.animal_max_width_mm.setText('max width (mm)')
        self.animal_max_width_mm.setRange(0,100_000)
        self.animal_max_width_mm.setValue(ANIMAL_TRACKING_PARAM['max_animal_width_mm'])
        
        self.animal_blur_sz_mm = LabeledDoubleSpinBox()
        self.animal_blur_sz_mm.setText('blur size (mm)')
        self.animal_blur_sz_mm.setRange(0,1000)
        self.animal_blur_sz_mm.setSingleStep(1/ANIMAL_TRACKING_PARAM['target_pix_per_mm'])
        self.animal_blur_sz_mm.setValue(ANIMAL_TRACKING_PARAM['blur_sz_mm'])

        self.animal_median_filter_sz_mm = LabeledDoubleSpinBox()
        self.animal_median_filter_sz_mm.setText('medfilt size (mm)')
        self.animal_median_filter_sz_mm.setRange(0,1000)
        self.animal_median_filter_sz_mm.setSingleStep(1/ANIMAL_TRACKING_PARAM['target_pix_per_mm'])
        self.animal_median_filter_sz_mm.setValue(ANIMAL_TRACKING_PARAM['median_filter_sz_mm'])
        
        self.body_pix_per_mm = LabeledDoubleSpinBox()
        self.body_pix_per_mm.setText('pix/mm')
        self.body_pix_per_mm.setRange(0,200)
        self.body_pix_per_mm.setValue(BODY_TRACKING_PARAM['pix_per_mm'])

        self.body_target_pix_per_mm = LabeledDoubleSpinBox()
        self.body_target_pix_per_mm.setText('target pix/mm')
        self.body_target_pix_per_mm.setRange(0,200)
        self.body_target_pix_per_mm.setValue(BODY_TRACKING_PARAM['target_pix_per_mm'])
        
        self.body_intensity = LabeledDoubleSpinBox()
        self.body_intensity.setText('intensity')
        self.body_intensity.setRange(0,1)
        self.body_intensity.setValue(BODY_TRACKING_PARAM['body_intensity'])
        
        self.body_brightness = LabeledDoubleSpinBox()
        self.body_brightness.setText('brightness')
        self.body_brightness.setRange(-1,1)
        self.body_brightness.setValue(BODY_TRACKING_PARAM['body_brightness'])
        
        self.body_gamma = LabeledDoubleSpinBox()
        self.body_gamma.setText('gamma')
        self.body_gamma.setRange(-10,10)
        self.body_gamma.setValue(BODY_TRACKING_PARAM['body_gamma'])
        
        self.body_contrast = LabeledDoubleSpinBox()
        self.body_contrast.setText('contrast')
        self.body_contrast.setRange(-10,10)
        self.body_contrast.setValue(BODY_TRACKING_PARAM['body_contrast'])
        
        self.body_min_size_mm = LabeledDoubleSpinBox()
        self.body_min_size_mm.setText('min area (mm2)')
        self.body_min_size_mm.setRange(0,100_000)
        self.body_min_size_mm.setValue(BODY_TRACKING_PARAM['min_body_size_mm'])
        
        self.body_max_size_mm = LabeledDoubleSpinBox()
        self.body_max_size_mm.setText('max area (mm2)')
        self.body_max_size_mm.setRange(0,100_000)
        self.body_max_size_mm.setValue(BODY_TRACKING_PARAM['max_body_size_mm'])
        
        self.body_min_length_mm = LabeledDoubleSpinBox()
        self.body_min_length_mm.setText('min length (mm)')
        self.body_min_length_mm.setRange(0,100_000)
        self.body_min_length_mm.setValue(BODY_TRACKING_PARAM['min_body_length_mm'])
        
        self.body_max_length_mm = LabeledDoubleSpinBox()
        self.body_max_length_mm.setText('max length (mm)')
        self.body_max_length_mm.setRange(0,100_000)
        self.body_max_length_mm.setValue(BODY_TRACKING_PARAM['max_body_length_mm'])
        
        self.body_min_width_mm = LabeledDoubleSpinBox()
        self.body_min_width_mm.setText('min width (mm)')
        self.body_min_width_mm.setRange(0,100_000)
        self.body_min_width_mm.setValue(BODY_TRACKING_PARAM['min_body_width_mm'])
        
        self.body_max_width_mm = LabeledDoubleSpinBox()
        self.body_max_width_mm.setText('max width (mm)')
        self.body_max_width_mm.setRange(0,100_000)
        self.body_max_width_mm.setValue(BODY_TRACKING_PARAM['max_body_width_mm'])
        
        self.body_blur_sz_mm = LabeledDoubleSpinBox()
        self.body_blur_sz_mm.setText('blur size (mm)')
        self.body_blur_sz_mm.setRange(0,1000)
        self.body_blur_sz_mm.setSingleStep(1/BODY_TRACKING_PARAM['target_pix_per_mm'])
        self.body_blur_sz_mm.setValue(BODY_TRACKING_PARAM['blur_sz_mm'])
        
        self.body_median_filter_sz_mm = LabeledDoubleSpinBox()
        self.body_median_filter_sz_mm.setText('medfilt size (mm)')
        self.body_median_filter_sz_mm.setRange(0,1000)
        self.body_median_filter_sz_mm.setSingleStep(1/BODY_TRACKING_PARAM['target_pix_per_mm'])
        self.body_median_filter_sz_mm.setValue(BODY_TRACKING_PARAM['median_filter_sz_mm'])

    def layout_components(self):
        animal = QVBoxLayout()
        animal.addStretch()
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
        body.addStretch()
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

        final = QHBoxLayout(self.window)
        final.addLayout(animal)
        final.addLayout(body)

    def on_change(self):
        self.updated = True

    def process_data(self, data: None) -> NDArray:
        self.app.processEvents()

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        # send tracking controls
        if self.updated:
            self.updated = False
            res = {}
            for i in range(N_TRACKER_WORKERS):
                res[f'tracker_control_{i}'] = {}
                res[f'tracker_control_{i}']['animal_tracking'] = {}
                res[f'tracker_control_{i}']['body_tracking'] = {}
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
                res[f'tracker_control_{i}']['body_tracking']['min_body_size_mm']=self.body_max_size_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['max_body_size_mm']=self.body_min_size_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['min_body_length_mm']=self.body_max_length_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['max_body_length_mm']=self.body_min_length_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['min_body_width_mm']=self.body_max_width_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['max_body_width_mm']=self.body_min_width_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['blur_sz_mm']=self.body_blur_sz_mm.value()
                res[f'tracker_control_{i}']['body_tracking']['median_filter_sz_mm']=self.body_median_filter_sz_mm.value()
            return res
