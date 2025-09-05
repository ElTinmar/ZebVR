from typing import Optional, Any, TypedDict,  Dict, Optional
from abc import ABC, abstractmethod
from enum import IntEnum
import time
import numpy as np
from numpy.typing import NDArray
from .debouncer import Debouncer
from qt_widgets import LabeledDoubleSpinBox, FileOpenLabeledEditButton, NDarray_to_QPixmap, CodeEditor
from image_tools import DrawPolyMaskDialog, im2uint8
import cv2
from pathlib import Path

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, 
    QStackedWidget, 
    QGroupBox, 
    QHBoxLayout,
    QVBoxLayout, 
    QComboBox,
    QLabel,
    QPushButton
)

class StopPolicy(IntEnum):
    PAUSE = 0
    TRIGGER = 1

    def __str__(self):
        return self.name

class TriggerType(IntEnum):
    SOFTWARE = 0
    TTL = 1
    TRACKING_MASK = 2
    TRACKING_CODE = 3

    def __str__(self):
        return self.name

class TriggerPolarity(IntEnum):
    RISING_EDGE = 0
    FALLING_EDGE = 1

    def __str__(self):
        return self.name

class TriggerDict(TypedDict):
    trigger: int 

class StopCondition(ABC):

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def done(self, metadata: Optional[Any]) -> bool:
        pass

class Pause(StopCondition):

    def __init__(self, pause_sec: float = 0) -> None:
        super().__init__()
        self.pause_sec = pause_sec
        self.time_start = 0

    def start(self) -> None:
        self.time_start = time.perf_counter()

    def done(self, metadata: Optional[Any]) -> bool:
        return (time.perf_counter() - self.time_start) >= self.pause_sec

class TTLTrigger(StopCondition):
    pass

class SoftwareTrigger(StopCondition):

    def __init__(
            self, 
            debouncer: Debouncer,
            polarity: TriggerPolarity = TriggerPolarity.RISING_EDGE,
        ) -> None:

        super().__init__()
        self.polarity = polarity
        self.debouncer = debouncer

    def start(self) -> None:
        pass

    def done(self, metadata: Optional[Any]) -> bool:

        output = False

        if metadata is None:
            return output

        try:
            value = metadata['trigger']
        except KeyError: 
            return output
        
        if value is None:
            return output
        
        transition = self.debouncer.update(value)
        if transition.name == self.polarity.name: 
            output = True
        return output

class TrackingTriggerMask(StopCondition):

    def __init__(
            self, 
            mask_file: str,
            debouncer = Debouncer,
            polarity: TriggerPolarity = TriggerPolarity.RISING_EDGE,
        ) -> None:

        super().__init__()

        self.mask_file = mask_file
        self.mask = np.load(mask_file)
        self.polarity = polarity
        self.debouncer = debouncer

    def start(self) -> None:
        pass
    
    def done(self, metadata: Optional[Any]) -> bool:

        output = False

        if metadata is None:
            return output
        
        try:
            identity = metadata['tracker_metadata']['identity']
            tracking = metadata['tracker_metadata']['tracking']

            fields = tracking.dtype.names
            if 'body' in fields and tracking['body']['success']:
                x, y = tracking['body']['centroid_global']
            else:
                x, y = tracking['animals']['centroids_global'][0,:]
            
            triggered = self.mask[int(y), int(x)]

        except Exception as e:
            return output
            
        transition = self.debouncer.update(triggered)
        if transition.name == self.polarity.name: 
            output = True

        return output
    
class TrackingTriggerCode(StopCondition):

    BASE_CODE = "def trigger_code(id, tracking) -> bool:\n    return False"

    def __init__(
            self, 
            code: str,
            debouncer = Debouncer,
            polarity: TriggerPolarity = TriggerPolarity.RISING_EDGE,
        ) -> None:

        super().__init__()

        self.code = code
        self.polarity = polarity
        self.debouncer = debouncer

    def start(self) -> None:
        pass
    
    def done(self, metadata: Optional[Any]) -> bool:

        output = False

        #print(self.code)

        if metadata is None:
            return output
        
        try:
            identity = metadata['tracker_metadata']['identity']
            tracking = metadata['tracker_metadata']['tracking']

            namespace = {}
            exec(self.code, namespace)
            triggered = namespace['trigger_code'](identity, tracking)

        except Exception as e:
            return output
            
        transition = self.debouncer.update(triggered)
        if transition.name == self.polarity.name: 
            output = True

        return output
    
    
class StopWidget(QWidget):

    state_changed = pyqtSignal()
    size_changed = pyqtSignal()
    MASK_PREVIEW_HEIGHT = 64
    
    def __init__(
            self, 
            debouncer: Debouncer,
            background_image: Optional[NDArray] = None,
            *args, 
            **kwargs
        ):
        
        super().__init__(*args, **kwargs)
        
        self.debouncer = debouncer
        self.background_image = background_image
        self.mask = None

        self.declare_components()
        self.layout_components()
        self.policy_changed()

    def declare_components(self) -> None:

        self.cmb_policy_select = QComboBox()
        for policy in StopPolicy:
            self.cmb_policy_select.addItem(str(policy))
        self.cmb_policy_select.currentIndexChanged.connect(self.policy_changed)

        self.pause_sec = LabeledDoubleSpinBox()
        self.pause_sec.setText('pause (sec):')
        self.pause_sec.setRange(0,100_000)
        self.pause_sec.setSingleStep(0.5)
        self.pause_sec.setValue(0)
        self.pause_sec.valueChanged.connect(self.state_changed.emit)

        self.cmb_trigger_select = QComboBox()
        for trigger in TriggerType:
            self.cmb_trigger_select.addItem(str(trigger))
        self.cmb_trigger_select.currentIndexChanged.connect(self.trigger_changed)

        self.cmb_trigger_polarity = QComboBox()
        for pol in TriggerPolarity:
            self.cmb_trigger_polarity.addItem(str(pol))
        self.cmb_trigger_polarity.currentIndexChanged.connect(self.state_changed)

        self.trigger_mask = FileOpenLabeledEditButton()
        self.trigger_mask.setLabel('load mask:')
        self.trigger_mask.textChanged.connect(self.load_mask)

        self.trigger_mask_button = QPushButton('draw mask')
        self.trigger_mask_button.clicked.connect(self.draw_trigger_mask)

        self.code_editor = CodeEditor()
        self.code_editor.textChanged.connect(self.state_changed)
        self.code_editor.setPlainText(TrackingTriggerCode.BASE_CODE)

        self.mask_image = QLabel() 

    def layout_components(self) -> None:

        software_trigger_layout = QVBoxLayout()
        software_trigger_layout.addStretch()
        self.software_trigger_group = QGroupBox('Sotware Trigger parameters')
        self.software_trigger_group.setLayout(software_trigger_layout)

        ttl_trigger_layout = QVBoxLayout()
        ttl_trigger_layout.addStretch()
        self.ttl_trigger_group = QGroupBox('TTL Trigger parameters')
        self.ttl_trigger_group.setLayout(ttl_trigger_layout)

        tracking_mask_trigger_ctrl = QVBoxLayout()
        tracking_mask_trigger_ctrl.addWidget(self.trigger_mask)
        tracking_mask_trigger_ctrl.addWidget(self.trigger_mask_button)
        tracking_mask_trigger = QHBoxLayout()
        tracking_mask_trigger.addLayout(tracking_mask_trigger_ctrl)
        tracking_mask_trigger.addWidget(self.mask_image)
        tracking_mask_trigger_layout = QVBoxLayout()
        tracking_mask_trigger_layout.addLayout(tracking_mask_trigger)
        tracking_mask_trigger_layout.addStretch()
        self.tracking_mask_trigger_group = QGroupBox('Tracking mask parameters')
        self.tracking_mask_trigger_group.setLayout(tracking_mask_trigger_layout)

        tracking_code_trigger_layout = QHBoxLayout()
        tracking_code_trigger_layout.addWidget(self.code_editor)
        self.tracking_code_trigger_group = QGroupBox('Tracking code parameters')
        self.tracking_code_trigger_group.setLayout(tracking_code_trigger_layout)

        self.trigger_stack = QStackedWidget()
        self.trigger_stack.addWidget(self.software_trigger_group)
        self.trigger_stack.addWidget(self.ttl_trigger_group)
        self.trigger_stack.addWidget(self.tracking_mask_trigger_group)
        self.trigger_stack.addWidget(self.tracking_code_trigger_group)

        trigger_container = QWidget()
        trigger_layout = QVBoxLayout(trigger_container)
        trigger_layout.addWidget(self.cmb_trigger_select)
        trigger_layout.addWidget(self.cmb_trigger_polarity)
        trigger_layout.addWidget(self.trigger_stack)
        trigger_layout.addStretch()
            
        self.policy_stack = QStackedWidget()
        self.policy_stack.addWidget(self.pause_sec)
        self.policy_stack.addWidget(trigger_container)

        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.cmb_policy_select)
        main_layout.addWidget(self.policy_stack)
        main_layout.addStretch()

    def set_background_image(self, image: NDArray) -> None:
        self.background_image = image

    def load_mask(self, filename):
        self.mask = np.load(filename)

        h, w = self.background_image.shape[:2]
        preview_width = int(w * self.MASK_PREVIEW_HEIGHT/h)
        image_resized = cv2.resize(
            im2uint8(self.mask),
            (preview_width, self.MASK_PREVIEW_HEIGHT), 
            cv2.INTER_NEAREST
        )
        self.mask_image.setPixmap(NDarray_to_QPixmap(image_resized))
        self.state_changed.emit()

    def draw_trigger_mask(self):
        if self.background_image is None:
            return
        
        dialog = DrawPolyMaskDialog(self.background_image)
        dialog.exec()
        self.mask = dialog.flatten()

        i = 0 
        filepath = Path(f'mask_{i:03}.npy')
        while filepath.exists():
            i += 1 
            filepath = Path(f'mask_{i:03}.npy')

        np.save(filepath, self.mask)
        self.trigger_mask.setText(str(filepath))
        self.state_changed.emit()

    def policy_changed(self):
        self.policy_stack.setCurrentIndex(self.cmb_policy_select.currentIndex())
        current_widget = self.policy_stack.currentWidget()
        if current_widget:
            new_height = current_widget.sizeHint().height()  
            self.policy_stack.setFixedHeight(new_height) 
            self.policy_stack.adjustSize()
            self.adjustSize() 
            self.size_changed.emit()
        self.state_changed.emit()

    def trigger_changed(self):
        self.trigger_stack.setCurrentIndex(self.cmb_trigger_select.currentIndex())
        self.state_changed.emit()

    def from_stop_condition(self, stop_condition: StopCondition) -> None:

        if isinstance(stop_condition, Pause):
            self.cmb_policy_select.setCurrentIndex(StopPolicy.PAUSE)
            self.pause_sec.setValue(stop_condition.pause_sec)

        elif isinstance(stop_condition, SoftwareTrigger):
            self.cmb_policy_select.setCurrentIndex(StopPolicy.TRIGGER)
            self.cmb_trigger_select.setCurrentIndex(TriggerType.SOFTWARE)
            self.cmb_trigger_polarity.setCurrentIndex(TriggerPolarity(stop_condition.polarity))

        elif isinstance(stop_condition, TrackingTriggerMask):
            self.cmb_policy_select.setCurrentIndex(StopPolicy.TRIGGER)
            self.cmb_trigger_select.setCurrentIndex(TriggerType.TRACKING_MASK)
            self.cmb_trigger_polarity.setCurrentIndex(TriggerPolarity(stop_condition.polarity))
            self.trigger_mask.setText(stop_condition.mask_file) 
            self.mask = stop_condition.mask

        elif isinstance(stop_condition, TrackingTriggerCode):
            self.cmb_policy_select.setCurrentIndex(StopPolicy.TRIGGER)
            self.cmb_trigger_select.setCurrentIndex(TriggerType.TRACKING_CODE)
            self.cmb_trigger_polarity.setCurrentIndex(TriggerPolarity(stop_condition.polarity))
            self.code_editor.setPlainText(stop_condition.code) 

    def to_stop_condition(self) -> StopCondition:

        state = self.get_state()

        stop_condition = None

        if state['stop_policy'] == StopPolicy.PAUSE:
            stop_condition = Pause(state['pause_sec'])

        if state['stop_policy'] == StopPolicy.TRIGGER:

            if state['trigger_select'] == TriggerType.SOFTWARE:
                stop_condition = SoftwareTrigger(
                    polarity = TriggerPolarity(state['trigger_polarity']),
                    debouncer = self.debouncer
                )

            if state['trigger_select'] == TriggerType.TTL:
                pass

            if state['trigger_select'] == TriggerType.TRACKING_MASK:
                stop_condition = TrackingTriggerMask(
                    mask_file = state['mask_file'],
                    polarity = TriggerPolarity(state['trigger_polarity']),
                    debouncer = self.debouncer
                )
            
            if state['trigger_select'] == TriggerType.TRACKING_CODE:
                stop_condition = TrackingTriggerCode(
                    code = state['code'],
                    polarity = TriggerPolarity(state['trigger_polarity']),
                    debouncer = self.debouncer
                )

        return stop_condition
    
    def get_state(self) -> Dict:
        state = {}
        state['stop_policy'] = self.cmb_policy_select.currentIndex()
        state['trigger_select'] = self.cmb_trigger_select.currentIndex()
        state['trigger_polarity'] = self.cmb_trigger_polarity.currentIndex()
        state['mask_file'] = self.trigger_mask.text()
        state['code'] = self.code_editor.toPlainText()
        state['pause_sec'] = self.pause_sec.value()
        return state
    
    def set_state(self, state: Dict) -> None:

        setters = {
            'stop_policy': self.cmb_policy_select.setCurrentIndex,
            'trigger_select': self.cmb_trigger_select.setCurrentIndex,
            'trigger_polarity': self.cmb_trigger_polarity.setCurrentIndex,
            'mask_file': self.trigger_mask.setText,
            'code': self.code_editor.setPlainText,
            'pause_sec': self.pause_sec.setValue
        }

        for key, setter in setters.items():
            if key in state:
                setter(state[key])