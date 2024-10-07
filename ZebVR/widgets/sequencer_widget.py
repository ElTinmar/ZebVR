from typing import Deque
from qt_widgets import LabeledDoubleSpinBox, QFileDialog
from collections import deque
import json
from collections import defaultdict
from typing import Dict, Optional, Deque, Tuple, DefaultDict
from abc import ABC, abstractmethod
from enum import IntEnum
import time

from PyQt5.QtWidgets import (
    QApplication,
    QWidget, 
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout, 
)

# TODO maybe this belongs somewhere else ? wait until refactoring of stim  shuffle 
class Stim(IntEnum):
    DARK = 0
    BRIGHT = 1
    PHOTOTAXIS = 2
    OMR = 3
    OKR = 4
    LOOMING = 5

class ProtocolItem(ABC):

    STIM_SELECT: Optional[int] = None

    @abstractmethod
    def run(self) -> Optional[DefaultDict]:
        pass

    def initialize(self):
        '''Run init steps in target worker process'''
        pass

    def cleanup(self):
        '''Run cleanup steps in target worker process'''
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, d: Dict) -> None:
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict:
        pass

# TODO implement this. maybe use keyboard module
'''
class ProtocolItemWaitKeyPress(ProtocolItem):

    def run(self) -> None:
        input('press Enter:') # input does not work in child process
        return None
'''

class ProtocolItemPause(ProtocolItem):

    def __init__(self, pause_sec: float) -> None:
        super().__init__()
        self.pause_sec = pause_sec

    def run(self) -> None:
        time.sleep(self.pause_sec)
        return None

    @classmethod
    def from_dict(cls, d: Dict):
        return cls(pause_sec = d['pause_sec'])

    def to_dict(self) -> Dict:
        res = {}
        res['type'] = 'pause'
        res['pause_sec'] = self.pause_sec
        return res

# TODO: implement trigger
"""
class ProtocolItemTrigger(ProtocolItem):

   def __init__(self, port: int) -> None:
       '''give info necessary to create DAQ object'''
       super().__init__()
       self.port = port

   def initialize(self):
        '''create DAQ object'''
        super().initialize()
        self.daq.open(port=self.port)
   
   def cleanup(self):
        '''create DAQ object'''
        super().cleanup()
        self.daq.close()
   
   def run(self) -> None:
       self.daq.wait_trigger()
       return None
"""

class ProtocolItemPhototaxis(ProtocolItem):

    STIM_SELECT = Stim.PHOTOTAXIS

    def __init__(
            self, 
            phototaxis_polarity: int,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float]
        ) -> None:

        super().__init__()
        self.phototaxis_polarity = phototaxis_polarity
        self.foreground_color = foreground_color
        self.background_color = background_color 

    def run(self) -> DefaultDict:
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'phototaxis_polarity': self.phototaxis_polarity,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'looming_center_mm': (0, 0)
        })
        return command 
    
    @classmethod
    def from_dict(cls, d: Dict) -> None:
        return cls(
            phototaxis_polarity = d['phototaxis_polarity'],
            foreground_color = d['foreground_color'],
            background_color = d['background_color']
        )

    def to_dict(self) -> Dict:
        res = {}
        res['type'] = 'phototaxis'
        res['phototaxis_polarity'] = self.phototaxis_polarity
        res['foreground_color'] = self.foreground_color
        res['background_color'] = self.background_color
        return res
    
class ProtocolItemOKR(ProtocolItem):

    STIM_SELECT = Stim.OKR

    def __init__(
            self, 
            okr_spatial_frequency_deg: float,
            okr_speed_deg_per_sec: float,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float]
        ) -> None:

        super().__init__()
        self.okr_spatial_frequency_deg = okr_spatial_frequency_deg
        self.okr_speed_deg_per_sec = okr_speed_deg_per_sec
        self.foreground_color = foreground_color
        self.background_color = background_color 

    def run(self) -> DefaultDict:
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'okr_spatial_frequency_deg': self.okr_spatial_frequency_deg,
            'okr_speed_deg_per_sec': self.okr_speed_deg_per_sec,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'looming_center_mm': (0, 0)
        })
        return command 

    @classmethod
    def from_dict(cls, d: Dict) -> None:
        return cls(
            okr_spatial_frequency_deg = d['okr_spatial_frequency_deg'],
            okr_speed_deg_per_sec = d['okr_speed_deg_per_sec'],
            foreground_color = d['foreground_color'],
            background_color = d['background_color']
        )

    def to_dict(self) -> Dict:
        res = {}
        res['type'] = 'OKR'
        res['okr_spatial_frequency_deg'] = self.okr_spatial_frequency_deg
        res['okr_speed_deg_per_sec'] = self.okr_speed_deg_per_sec
        res['foreground_color'] = self.foreground_color
        res['background_color'] = self.background_color
        return res
    
class ProtocolItemOMR(ProtocolItem):
    
    STIM_SELECT = Stim.OMR
    
    def __init__(
            self, 
            omr_spatial_period_mm: float,
            omr_angle_deg: float,
            omr_speed_mm_per_sec: float,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float]
        ) -> None:

        super().__init__()
        self.omr_spatial_period_mm = omr_spatial_period_mm
        self.omr_angle_deg = omr_angle_deg
        self.omr_speed_mm_per_sec = omr_speed_mm_per_sec
        self.foreground_color = foreground_color
        self.background_color = background_color 

    def run(self) -> DefaultDict:
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'omr_spatial_period_mm': self.omr_spatial_period_mm,
            'omr_angle_deg': self.omr_angle_deg,
            'omr_speed_mm_per_sec': self.omr_speed_mm_per_sec,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'looming_center_mm': (0, 0)
        })
        return command 

    @classmethod
    def from_dict(cls, d: Dict) -> None:
        return cls(
            omr_spatial_period_mm = d['omr_spatial_period_mm'],
            omr_angle_deg = d['omr_angle_deg'],
            omr_speed_mm_per_sec = d['omr_speed_mm_per_sec'],
            foreground_color = d['foreground_color'],
            background_color = d['background_color']
        )

    def to_dict(self) -> Dict:
        res = {}
        res['type'] = 'OMR'
        res['omr_spatial_period_mm'] = self.omr_spatial_period_mm
        res['omr_angle_deg'] = self.omr_angle_deg
        res['omr_speed_mm_per_sec'] = self.omr_speed_mm_per_sec
        res['foreground_color'] = self.foreground_color
        res['background_color'] = self.background_color
        return res
    
class ProtocolItemDark(ProtocolItem):

    STIM_SELECT = Stim.DARK

    def __init__(
            self,
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float]
        ) -> None:

        super().__init__()
        self.foreground_color = foreground_color
        self.background_color = background_color 

    def run(self) -> DefaultDict:
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'looming_center_mm': (0, 0)
        })
        return command 

    @classmethod
    def from_dict(cls, d: Dict) -> None:
        return cls(
            foreground_color = d['foreground_color'],
            background_color = d['background_color']
        )

    def to_dict(self) -> Dict:
        res = {}
        res['type'] = 'dark'
        res['foreground_color'] = self.foreground_color
        res['background_color'] = self.background_color
        return res

class ProtocolItemBright(ProtocolItem):

    STIM_SELECT = Stim.BRIGHT

    def __init__(
            self, 
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float]
        ) -> None:

        super().__init__()
        self.foreground_color = foreground_color 
        self.background_color = background_color 

    def run(self) -> DefaultDict:
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'looming_center_mm': (0, 0)
        })
        return command 
    
    @classmethod
    def from_dict(cls, d: Dict) -> None:
        return cls(
            foreground_color = d['foreground_color'],
            background_color = d['background_color']
        )

    def to_dict(self) -> Dict:
        res = {}
        res['type'] = 'bright'
        res['foreground_color'] = self.foreground_color
        res['background_color'] = self.background_color
        return res

class ProtocolItemLooming(ProtocolItem):

    STIM_SELECT = Stim.LOOMING

    def __init__(
            self, 
            foreground_color: Tuple[float, float, float, float],
            background_color: Tuple[float, float, float, float],
            looming_center_mm: Tuple[float, float],
            looming_period_sec: float,
            looming_expansion_time_sec: float,
            looming_expansion_speed_mm_per_sec: float   
        ) -> None:

        super().__init__()
        self.foreground_color = foreground_color 
        self.background_color = background_color
        self.looming_center_mm = looming_center_mm
        self.looming_period_sec = looming_period_sec 
        self.looming_expansion_time_sec = looming_expansion_time_sec
        self.looming_expansion_speed_mm_per_sec = looming_expansion_speed_mm_per_sec

    def run(self) -> DefaultDict:
        command = defaultdict(float, {
            'stim_select': self.STIM_SELECT,
            'looming_center_mm': self.looming_center_mm,
            'looming_period_sec': self.looming_period_sec,
            'looming_expansion_time_sec': self.looming_expansion_time_sec,
            'looming_expansion_speed_mm_per_sec': self.looming_expansion_speed_mm_per_sec,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
        })
        return command 

    @classmethod
    def from_dict(cls, d: Dict) -> None:
        return cls(
            foreground_color = d['foreground_color'],
            background_color = d['background_color'],
            looming_center_mm = d['looming_center_mm'],
            looming_period_sec = d['looming_period_sec'],
            looming_expansion_time_sec = d['looming_expansion_time_sec'],
            looming_expansion_speed_mm_per_sec = d['looming_expansion_speed_mm_per_sec']
        )

    def to_dict(self) -> Dict:
        res = {}
        res['type'] = 'looming'
        res['looming_center_mm'] = self.looming_center_mm
        res['looming_period_sec'] = self.looming_period_sec
        res['looming_expansion_time_sec'] = self.looming_expansion_time_sec
        res['looming_expansion_speed_mm_per_sec'] = self.looming_expansion_speed_mm_per_sec
        res['foreground_color'] = self.foreground_color
        res['background_color'] = self.background_color
        return res
    
from ZebVR.widgets import StimWidget

class SequencerItem(QWidget):

    def set_protocol_item(self, p: ProtocolItem) -> None:
        pass

    def get_protocol_item(self) -> ProtocolItem:
        pass

class PauseSequencerItem(SequencerItem):

    def __init__(self,*args,**kwargs):
        
        super().__init__(*args,**kwargs)

        self.pause_sec = LabeledDoubleSpinBox()
        self.pause_sec.setText('pause (sec):')
        self.pause_sec.setRange(0,100_000)
        self.pause_sec.setSingleStep(0.5)
        self.pause_sec.setValue(0)

        layout = QHBoxLayout(self)
        layout.addWidget(self.pause_sec)

    def set_protocol_item(self, p: ProtocolItemPause):
        self.pause_sec.setValue(p.pause_sec)
    
    def get_protocol_item(self) -> ProtocolItemPause:
        protocol = ProtocolItemPause(
            pause_sec=self.pause_sec.value()
        ) 
        return protocol
    
class StimSequencerItem(SequencerItem, StimWidget):
    
    def set_protocol_item(self, item: ProtocolItem):   

        self.sb_foreground_color_R.setValue(item.foreground_color[0])
        self.sb_foreground_color_G.setValue(item.foreground_color[1])
        self.sb_foreground_color_B.setValue(item.foreground_color[2])
        self.sb_foreground_color_A.setValue(item.foreground_color[3])
        
        self.sb_background_color_R.setValue(item.background_color[0])
        self.sb_background_color_G.setValue(item.background_color[1])
        self.sb_background_color_B.setValue(item.background_color[2])
        self.sb_background_color_A.setValue(item.background_color[3])         
        
        if isinstance(item, ProtocolItemBright):
            self.cmb_stim_select.setCurrentText('Bright')

        elif isinstance(item, ProtocolItemDark):
            self.cmb_stim_select.setCurrentText('Dark')

        elif isinstance(item, ProtocolItemPhototaxis):
            self.cmb_stim_select.setCurrentText('Phototaxis')
            self.chb_phototaxis_polarity.setChecked(item.phototaxis_polarity == 1) 

        elif isinstance(item, ProtocolItemOMR):
            self.cmb_stim_select.setCurrentText('OMR')
            self.sb_omr_spatial_freq.setValue(item.omr_spatial_period_mm)
            self.sb_omr_angle.setValue(item.omr_angle_deg)
            self.sb_omr_speed.setValue(item.omr_speed_mm_per_sec)  
    
        elif isinstance(item, ProtocolItemOKR):
            self.cmb_stim_select.setCurrentText('OKR')
            self.sb_okr_spatial_freq.setValue(item.okr_spatial_frequency_deg)
            self.sb_okr_speed.setValue(item.okr_speed_deg_per_sec) 
    
        elif isinstance(item, ProtocolItemLooming):
            self.cmb_stim_select.setCurrentText('Looming')
            self.sb_looming_center_mm_x.setValue(item.looming_center_mm[0])
            self.sb_looming_center_mm_y.setValue(item.looming_center_mm[1])
            self.sb_looming_period_sec.setValue(item.looming_period_sec)
            self.sb_looming_expansion_time_sec.setValue(item.looming_expansion_time_sec)
            self.sb_looming_expansion_speed_mm_per_sec.setValue(item.looming_expansion_speed_mm_per_sec)

    def get_protocol_item(self) -> ProtocolItem:

        if self.cmb_stim_select.currentText() == 'Dark':
            protocol = ProtocolItemDark(
                foreground_color = (
                    self.sb_foreground_color_R.value(), 
                    self.sb_foreground_color_G.value(),
                    self.sb_foreground_color_B.value(),
                    self.sb_foreground_color_A.value()
                ),
                background_color = (
                    self.sb_background_color_R.value(), 
                    self.sb_background_color_G.value(),
                    self.sb_background_color_B.value(),
                    self.sb_background_color_A.value()
                )
            )

        if self.cmb_stim_select.currentText() == 'Bright':
            protocol = ProtocolItemBright(
                foreground_color = (
                    self.sb_foreground_color_R.value(), 
                    self.sb_foreground_color_G.value(),
                    self.sb_foreground_color_B.value(),
                    self.sb_foreground_color_A.value()
                ),
                background_color = (
                    self.sb_background_color_R.value(), 
                    self.sb_background_color_G.value(),
                    self.sb_background_color_B.value(),
                    self.sb_background_color_A.value()
                )
            )

        if self.cmb_stim_select.currentText() == 'Phototaxis':
            protocol = ProtocolItemPhototaxis(
                foreground_color = (
                    self.sb_foreground_color_R.value(), 
                    self.sb_foreground_color_G.value(),
                    self.sb_foreground_color_B.value(),
                    self.sb_foreground_color_A.value()
                ),
                background_color = (
                    self.sb_background_color_R.value(), 
                    self.sb_background_color_G.value(),
                    self.sb_background_color_B.value(),
                    self.sb_background_color_A.value()
                ),
                phototaxis_polarity=-1+2*self.chb_phototaxis_polarity.isChecked()
            )

        if self.cmb_stim_select.currentText() == 'OMR':
            protocol = ProtocolItemOMR(
                foreground_color = (
                    self.sb_foreground_color_R.value(), 
                    self.sb_foreground_color_G.value(),
                    self.sb_foreground_color_B.value(),
                    self.sb_foreground_color_A.value()
                ),
                background_color = (
                    self.sb_background_color_R.value(), 
                    self.sb_background_color_G.value(),
                    self.sb_background_color_B.value(),
                    self.sb_background_color_A.value()
                ),
                omr_spatial_period_mm = self.sb_omr_spatial_freq.value(),
                omr_angle_deg =self.sb_omr_angle.value(),
                omr_speed_mm_per_sec = self.sb_omr_speed.value() 
            )

        if self.cmb_stim_select.currentText() == 'OKR':
            protocol = ProtocolItemOKR(
                foreground_color = (
                    self.sb_foreground_color_R.value(), 
                    self.sb_foreground_color_G.value(),
                    self.sb_foreground_color_B.value(),
                    self.sb_foreground_color_A.value()
                ),
                background_color = (
                    self.sb_background_color_R.value(), 
                    self.sb_background_color_G.value(),
                    self.sb_background_color_B.value(),
                    self.sb_background_color_A.value()
                ),
                okr_spatial_frequency_deg = self.sb_okr_spatial_freq.value(),
                okr_speed_deg_per_sec = self.sb_okr_speed.value()
            )

        if self.cmb_stim_select.currentText() == 'Looming':
            protocol = ProtocolItemLooming(
                foreground_color = (
                    self.sb_foreground_color_R.value(), 
                    self.sb_foreground_color_G.value(),
                    self.sb_foreground_color_B.value(),
                    self.sb_foreground_color_A.value()
                ),
                background_color = (
                    self.sb_background_color_R.value(), 
                    self.sb_background_color_G.value(),
                    self.sb_background_color_B.value(),
                    self.sb_background_color_A.value()
                ),
                looming_center_mm = (
                    self.sb_looming_center_mm_x.value(),
                    self.sb_looming_center_mm_y.value()
                ),
                looming_period_sec = self.sb_looming_period_sec.value(),
                looming_expansion_time_sec = self.sb_looming_expansion_time_sec.value(),
                looming_expansion_speed_mm_per_sec = self.sb_looming_expansion_speed_mm_per_sec.value()
            )
        
        return protocol

class TriggerSequencerItem(SequencerItem):
    pass

class SequencerWidget(QWidget):

    def __init__(
            self,
            *args,
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.declare_components()
        self.layout_components()
        self.setWindowTitle('Sequencer')

    def declare_components(self) -> None:

        # QListWidget
        self.list = QListWidget()
        self.list.setFixedWidth(460)
        self.list.setFixedHeight(720)
        self.list.setAlternatingRowColors(True)

        #self.list.setSpacing(5)

        # add stim button
        self.btn_add_stim = QPushButton('stim')
        self.btn_add_stim.clicked.connect(self.stim_pressed)

        # add pause button
        self.btn_add_pause = QPushButton('pause')
        self.btn_add_pause.clicked.connect(self.pause_pressed)
        
        # add trigger button 
        self.btn_add_trigger = QPushButton('trigger')
        self.btn_add_trigger.clicked.connect(self.trigger_pressed)
        self.btn_add_trigger.setEnabled(False)

        # remove button
        self.btn_remove = QPushButton('remove')
        self.btn_remove.clicked.connect(self.remove_pressed)

        self.btn_load = QPushButton('load')
        self.btn_load.clicked.connect(self.load)

        self.btn_save = QPushButton('save')
        self.btn_save.clicked.connect(self.save)

    def layout_components(self) -> None:
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_add_stim)
        btn_layout.addWidget(self.btn_add_pause)
        btn_layout.addWidget(self.btn_add_trigger)
        btn_layout.addWidget(self.btn_remove)

        io_layout = QHBoxLayout()
        io_layout.addWidget(self.btn_load)
        io_layout.addWidget(self.btn_save)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(self.list)
        main_layout.addLayout(io_layout)

    def stim_pressed(self):
        stim = StimSequencerItem()
        item = QListWidgetItem()
        item.setSizeHint(stim.sizeHint())
        self.list.addItem(item)
        self.list.setItemWidget(item, stim)

    def pause_pressed(self):
        pause = PauseSequencerItem()
        item = QListWidgetItem()
        item.setSizeHint(pause.sizeHint())
        self.list.addItem(item)
        self.list.setItemWidget(item, pause)

    def trigger_pressed(self):
        trigger = TriggerSequencerItem()
        item = QListWidgetItem()
        item.setSizeHint(trigger.sizeHint())
        self.list.addItem(item)
        self.list.setItemWidget(item, trigger)

    def remove_pressed(self):
        selected_items = self.list.selectedItems()
        for item in selected_items:
            row = self.list.row(item)
            self.list.takeItem(row)

    def get_protocol(self) -> Deque[ProtocolItem]:
        state = deque()
        num_items = self.list.count()
        for row in range(num_items):
            item = self.list.item(row)
            widget = self.list.itemWidget(item)
            state.append(widget.get_protocol_item())
        return state
    
    def get_protocol_duration(self):
        pause_duration = 0
        num_items = self.list.count()
        for row in range(num_items):
            item = self.list.item(row)
            widget = self.list.itemWidget(item)
            protocol_item = widget.get_protocol_item()
            if isinstance(protocol_item, ProtocolItemPause):
                data = protocol_item.to_dict()
                pause_duration += data['pause_sec']
        return pause_duration

    def load(self):

        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "Load file",
            "protocol.json",
            "JSON file (*.json)"
        )

        with open(filename, 'r') as fp:
            state = json.load(fp)

        for element in state:

            sequencer_item = StimSequencerItem
            if element['type'] == 'pause':
                protocol_item = ProtocolItemPause.from_dict(element)
                sequencer_item = PauseSequencerItem
            elif element['type'] == 'dark':
                protocol_item = ProtocolItemDark.from_dict(element)
            elif element['type'] == 'bright':
                protocol_item = ProtocolItemBright.from_dict(element)
            elif element['type'] == 'phototaxis':
                protocol_item = ProtocolItemPhototaxis.from_dict(element)
            elif element['type'] == 'OMR':
                protocol_item = ProtocolItemOMR.from_dict(element)
            elif element['type'] == 'OKR':
                protocol_item = ProtocolItemOKR.from_dict(element)
            elif element['type'] == 'looming':
                protocol_item = ProtocolItemLooming.from_dict(element)

            sequencer = sequencer_item()
            sequencer.set_protocol_item(protocol_item)
            item = QListWidgetItem()
            item.setSizeHint(sequencer.sizeHint())
            self.list.addItem(item)
            self.list.setItemWidget(item, sequencer)

    def save(self):

        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Save file",
            "protocol.json",
            "JSON file (*.json)"
        )

        state = []
        num_items = self.list.count()
        for row in range(num_items):
            item = self.list.item(row)
            widget = self.list.itemWidget(item)
            protocol_item = widget.get_protocol_item()
            state.append(protocol_item.to_dict())

        with open(filename, 'w') as fp:
            json.dump(state, fp)

if __name__ == '__main__':

    app = QApplication([])
    window = SequencerWidget()
    window.show()
    app.exec()

    print(window.get_protocol())