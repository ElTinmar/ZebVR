from typing import Dict, Tuple
from qt_widgets import LabeledDoubleSpinBox
from collections import deque

from PyQt5.QtWidgets import (
    QApplication,
    QWidget, 
    QListWidget,
    QListWidgetItem,
    QPushButton,
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
    ProtocolItemDark,
    ProtocolItemBright,
    ProtocolItemOKR,
    ProtocolItemOMR,
    ProtocolItemPhototaxis,
    ProtocolItemPause
)

from ZebVR.widgets import StimWidget

class PauseWidget(QWidget):

    def __init__(self,*args,**kwargs):
        
        super().__init__(*args,**kwargs)

        self.pause_sec = LabeledDoubleSpinBox(self)
        self.pause_sec.setText('pause (sec):')
        self.pause_sec.setRange(0,100_000)
        self.pause_sec.setSingleStep(0.5)
        self.pause_sec.setValue(0)

class TriggerWidget(QWidget):
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
        stim = StimWidget()
        item = QListWidgetItem()
        item.setSizeHint(stim.sizeHint())
        self.list.addItem(item)
        self.list.setItemWidget(item, stim)

    def pause_pressed(self):
        pause = PauseWidget()
        item = QListWidgetItem()
        item.setSizeHint(pause.sizeHint())
        self.list.addItem(item)
        self.list.setItemWidget(item, pause)

    def trigger_pressed(self):
        trigger = TriggerWidget()
        item = QListWidgetItem()
        item.setSizeHint(trigger.sizeHint())
        self.list.addItem(item)
        self.list.setItemWidget(item, trigger)

    def remove_pressed(self):
        selected_items = self.list.selectedItems()
        for item in selected_items:
            row = self.list.row(item)
            self.list.takeItem(row)

    def get_state(self):
        # return ProtocolItem deque to use with Protocol Worker  
        pass

if __name__ == '__main__':

    app = QApplication([])
    window = SequencerWidget()
    window.show()
    app.exec()