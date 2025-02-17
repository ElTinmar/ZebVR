from typing import Deque
from qt_widgets import LabeledSpinBox
from collections import deque
from typing import Deque, Dict, Optional
import random

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QWidget, 
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QHBoxLayout,
    QVBoxLayout
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

        self.spb_repetitions = LabeledSpinBox()
        self.spb_repetitions.setText('repetitions')
        self.spb_repetitions.setRange(1,1_000)
        self.spb_repetitions.setValue(1)
        self.spb_repetitions.valueChanged.connect(self.state_changed.emit)

    def layout_components(self) -> None:
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.btn_add_stim)
        btn_layout.addWidget(self.btn_remove)

        control_layout = QHBoxLayout()
        control_layout.addWidget(self.spb_repetitions)
        control_layout.addStretch()
        control_layout.addWidget(self.btn_shuffle)

        main_layout = QVBoxLayout(self)
        main_layout.addLayout(btn_layout)
        main_layout.addWidget(self.list)
        main_layout.addLayout(control_layout)

    def on_size_change(self):
        for i in range(self.list.count()):
            item = self.list.item(i)
            stim = self.list.itemWidget(item)
            item.setSizeHint(stim.sizeHint())
        
    def shuffle(self):

        items = [self.list.item(i) for i in range(self.list.count())]
        widgets = [self.list.itemWidget(item) for item in items]
        states = [widget.get_state() for widget in widgets]

        random.shuffle(states)
        
        for item in items:
            row = self.list.row(item)
            item = self.list.takeItem(row)
            del item

        for state in states:
            new_widget = StimWidget()
            new_widget.set_state(state)
            new_widget.state_changed.connect(self.state_changed.emit)
            new_widget.size_changed.connect(self.on_size_change)
            new_item = QListWidgetItem()
            new_item.setSizeHint(new_widget.sizeHint())
            self.list.addItem(new_item)
            self.list.setItemWidget(new_item, new_widget)

        self.state_changed.emit()

    def stim_pressed(self):
        self.add_stim_widget(None)

    def remove_pressed(self):
        selected_items = self.list.selectedItems()
        for item in selected_items:
            row = self.list.row(item)
            item = self.list.takeItem(row)
            del item

        self.state_changed.emit()

    def get_protocol(self) -> Deque[ProtocolItem]:
        protocol = deque()
        num_items = self.list.count()
        for row in range(num_items):
            item = self.list.item(row)
            widget = self.list.itemWidget(item)
            protocol.append(widget.get_protocol_item())
        return protocol
    
    def add_stim_widget(self, protocol_item: Optional[ProtocolItem]):

        stim = StimWidget()
        stim.state_changed.connect(self.state_changed.emit)
        stim.size_changed.connect(self.on_size_change)

        if protocol_item is not None:
            stim.from_protocol_item(protocol_item)

        item = QListWidgetItem()
        item.setSizeHint(stim.sizeHint())

        self.list.addItem(item)
        self.list.setItemWidget(item, stim)

        self.state_changed.emit()
    
    def set_protocol(self, protocol: Deque[ProtocolItem]) -> None:
        for protocol_item in protocol:
            self.add_stim_widget(protocol_item)

    def get_state(self) -> Dict:
        state = {}
        state['repetitions'] = self.spb_repetitions.value()
        state['protocol'] = self.get_protocol()
        return state

    def set_state(self, state: Dict) -> None:
        self.spb_repetitions.setValue(state['repetitions'])
        self.set_protocol(state['protocol'])

if __name__ == '__main__':

    app = QApplication([])
    window = SequencerWidget()
    window.show()
    app.exec()

    print(window.get_protocol())