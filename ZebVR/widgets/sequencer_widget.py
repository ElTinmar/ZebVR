from typing import Deque
from qt_widgets import LabeledSpinBox
from collections import deque
from typing import Deque

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QWidget, 
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout, 
)
from .protocol_widget import StimWidget
from ..protocol import ProtocolItem
class SequencerWidget(QWidget):

    state_changed = pyqtSignal()

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
        self.list.setAlternatingRowColors(True)

        # add stim button
        self.btn_add_stim = QPushButton('stim')
        self.btn_add_stim.clicked.connect(self.stim_pressed)

        # remove button
        self.btn_remove = QPushButton('remove')
        self.btn_remove.clicked.connect(self.remove_pressed)

        self.btn_shuffle = QPushButton('shuffle')
        self.btn_shuffle.clicked.connect(self.shuffle)
        self.btn_shuffle.setEnabled(False)

        self.spb_loop = LabeledSpinBox()
        self.spb_loop.setText('loop')
        self.spb_loop.setRange(-1,1_000)
        self.spb_loop.setValue(0)
        self.spb_loop.setToolTip('A value of -1 loops forever') 
        self.spb_loop.setEnabled(False)

    def layout_components(self) -> None:
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_add_stim)
        btn_layout.addWidget(self.btn_remove)

        control_layout = QHBoxLayout()
        control_layout.addWidget(self.spb_loop)
        control_layout.addStretch()
        control_layout.addWidget(self.btn_shuffle)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(self.list)
        main_layout.addLayout(control_layout)

    def shuffle(self):
        pass

    def stim_pressed(self):
        stim = StimWidget()
        stim.state_changed.connect(self.state_changed.emit)
        item = QListWidgetItem()
        item.setSizeHint(stim.sizeHint())
        self.list.addItem(item)
        self.list.setItemWidget(item, stim)
        self.state_changed.emit()

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
    
    def set_protocol(self, protocol: Deque[ProtocolItem]) -> None:
        for protocol_item in protocol:
            stim = StimWidget()
            stim.set_protocol_item(protocol_item)
            item = QListWidgetItem()
            item.setSizeHint(stim.sizeHint())
            self.list.addItem(item)
            self.list.setItemWidget(item, stim)
        self.state_changed.emit()

    def get_recording_duration(self): # TODO change this
        return 60

if __name__ == '__main__':

    app = QApplication([])
    window = SequencerWidget()
    window.show()
    app.exec()

    print(window.get_protocol())