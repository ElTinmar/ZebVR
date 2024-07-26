from typing import Dict, Tuple, List
from qt_widgets import LabeledDoubleSpinBox
from collections import deque

from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication,
    QWidget, 
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QFrame,
    QCheckBox, 
    QStackedWidget, 
    QGroupBox, 
    QHBoxLayout,
    QVBoxLayout, 
    QLayout,
    QComboBox,
    QLabel
)

# TODO should that really be in workers?
from ZebVR.workers import (
    ProtocolItem,
    ProtocolItemDark,
    ProtocolItemBright,
    ProtocolItemOKR,
    ProtocolItemOMR,
    ProtocolItemPhototaxis,
    ProtocolItemLooming,
    ProtocolItemPause
)

from ZebVR.widgets import StimWidget

class SequencerItem(QWidget):

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
    
    def get_protocol_item(self) -> ProtocolItem:
        protocol = ProtocolItemPause(
            pause_sec=self.pause_sec.value()
        ) 
        return protocol
    
class StimSequencerItem(SequencerItem, StimWidget):

    def get_protocol_item(self) -> ProtocolItem:

        if self.cmb_stim_select.currentText() == 'Dark':
            protocol = ProtocolItemDark(
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
                looming_center_mm_x = self.sb_looming_center_mm_x.value(),
                looming_center_mm_y = self.sb_looming_center_mm_y.value(),
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

    def layout_components(self) -> None:
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_add_stim)
        btn_layout.addWidget(self.btn_add_pause)
        btn_layout.addWidget(self.btn_add_trigger)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(self.list)
        main_layout.addWidget(self.btn_remove)

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

    def get_state(self) -> List:
        state = deque()
        num_items = self.list.count()
        for row in range(num_items):
            item = self.list.item(row)
            widget = self.list.itemWidget(item)
            state.append(widget.get_protocol_item())
        return state

if __name__ == '__main__':

    app = QApplication([])
    window = SequencerWidget()
    window.show()
    app.exec()

    print(window.get_state())