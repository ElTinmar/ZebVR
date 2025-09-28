from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QTreeWidget, QTreeWidgetItem, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal
from qt_widgets import LabeledSpinBox

from .protocol_widget import StimWidget
from ..protocol import ProtocolItem, Debouncer
from daq_tools import (
    BoardInfo,
    BoardType
)
import numpy as np
from numpy.typing import NDArray
from pathlib import Path
from typing import List, Dict, Deque, Optional
from collections import deque

class LoopWidget(LabeledSpinBox):

    def __init__(self):
        super().__init__()
        self.setValue(1)
        self.setText("Repetitions:")

class SequencerWidget(QWidget):

    state_changed = pyqtSignal()
    DEFAULT_DEBOUNCER_LENGTH = 5
    DEFAULT_BACKGROUND_FILE: Path = Path('ZebVR/default/background.npy')

    def __init__(
            self,
            daq_boards: Dict[BoardType, List[BoardInfo]] = {},
            *args,
            **kwargs
        ):

        super().__init__(*args, **kwargs)

        self.debouncer = Debouncer(self.DEFAULT_DEBOUNCER_LENGTH)
        self.daq_boards = daq_boards
        self.background_image = None
        if self.DEFAULT_BACKGROUND_FILE.exists():
            self.background_image = np.load(self.DEFAULT_BACKGROUND_FILE)

        self.declare_components()
        self.layout_components()
        self.setWindowTitle("Sequencer")

    def declare_components(self):
        
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAlternatingRowColors(True)
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDragDropMode(QTreeWidget.InternalMove)
        self.tree.setDefaultDropAction(Qt.MoveAction)
        self.tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.tree.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.tree.verticalScrollBar().setSingleStep(2)
        self.tree.setIndentation(60)

        self.root_item = QTreeWidgetItem(self.tree)
        self.tree.addTopLevelItem(self.root_item)
        self.root_widget = LoopWidget()
        self.tree.setItemWidget(self.root_item, 0, self.root_widget)
        
        self.spb_debouncer_length = LabeledSpinBox()
        self.spb_debouncer_length.setText('debouncer length')
        self.spb_debouncer_length.setRange(1,1_000)
        self.spb_debouncer_length.setValue(self.DEFAULT_DEBOUNCER_LENGTH)
        self.spb_debouncer_length.valueChanged.connect(self.update_debouncer)

        self.btn_add_stim = QPushButton("Add Stim")
        self.btn_add_loop = QPushButton("Add Loop")
        self.btn_remove = QPushButton("Remove Selected")
        self.btn_move_up = QPushButton("Move Up")
        self.btn_move_down = QPushButton("Move Down")

        self.btn_add_stim.clicked.connect(self.stim_pressed)
        self.btn_add_loop.clicked.connect(self.add_loop)
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_move_up.clicked.connect(self.move_up)
        self.btn_move_down.clicked.connect(self.move_down)
    
    def layout_components(self):
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.spb_debouncer_length)
        layout.addWidget(self.tree)
        layout.addWidget(self.btn_add_stim)
        layout.addWidget(self.btn_add_loop)
        layout.addWidget(self.btn_remove)
        layout.addWidget(self.btn_move_up)
        layout.addWidget(self.btn_move_down)

    def update_debouncer(self, value: int) -> None:
        self.debouncer.set_buffer_length(value)
        self.state_changed.emit()

    def set_daq_boards(self, daq_boards: Dict[BoardType, List[BoardInfo]]):

        def update_item(item: QTreeWidgetItem):

            widget = self.tree.itemWidget(item, 0)
            if isinstance(widget, StimWidget):
                widget.blockSignals(True)
                widget.set_daq_boards(self.daq_boards)
                widget.blockSignals(False)

            for i in range(item.childCount()):
                update_item(item.child(i))

        self.daq_boards = daq_boards
        update_item(self.root_item)
        self.state_changed.emit()

    def set_background_image(self, image: NDArray) -> None:

        def update_item(item: QTreeWidgetItem):

            widget = self.tree.itemWidget(item, 0)
            if isinstance(widget, StimWidget):
                widget.set_background_image(image)
            for i in range(item.childCount()):
                update_item(item.child(i))

        self.background_image = image
        update_item(self.root_item)

    def on_size_change(self):

        def update_item(item: QTreeWidgetItem):

            widget = self.tree.itemWidget(item, 0)
            if widget is not None:
                item.setSizeHint(0, widget.sizeHint())
            for i in range(item.childCount()):
                update_item(item.child(i))

        update_item(self.root_item)
        self.tree.doItemsLayout()

    def _selected_or_root(self):

        items = self.tree.selectedItems()
        return items[0] if items else self.root_item

    def _normalize_parent(self, parent_item):

        widget = self.tree.itemWidget(parent_item, 0)
        if isinstance(widget, StimWidget):
            return parent_item.parent() or self.root_item
        return parent_item

    def stim_pressed(self):
        self.add_stim_widget()
        
    def add_stim_widget(self, protocol_item: Optional[ProtocolItem] = None):

        stim_widget = StimWidget(self.debouncer, self.daq_boards, self.background_image)
        stim_widget.state_changed.connect(self.state_changed)
        stim_widget.size_changed.connect(self.on_size_change)

        if protocol_item is not None:
            stim_widget.from_protocol_item(protocol_item)

        parent_item = self._normalize_parent(self._selected_or_root())
        item = QTreeWidgetItem(parent_item)
        self.tree.setItemWidget(item, 0, stim_widget)
        parent_item.setExpanded(True)

        self.state_changed.emit()

    def add_loop(self):

        parent_item = self._normalize_parent(self._selected_or_root())
        item = QTreeWidgetItem(parent_item)
        self.tree.setItemWidget(item, 0, LoopWidget())
        parent_item.setExpanded(True)

    def remove_selected(self):

        items = self.tree.selectedItems()
        if not items:
            return
        item = items[0]
        if item is self.root_item:
            print("Cannot remove root loop.")
            return
        parent = item.parent() or self.tree.invisibleRootItem()
        parent.takeChild(parent.indexOfChild(item))

    def clone_item(self, item, parent, index):

        new_item = QTreeWidgetItem()
        parent.insertChild(index, new_item)   

        old_widget = self.tree.itemWidget(item, 0)
        if isinstance(old_widget, StimWidget):
            new_widget = StimWidget(self.debouncer, self.daq_boards, self.background_image)
            new_widget.state_changed.connect(self.state_changed)
            new_widget.size_changed.connect(self.on_size_change)
            new_widget.set_state(old_widget.get_state())
            self.tree.setItemWidget(new_item, 0, new_widget)

        elif isinstance(old_widget, LoopWidget):
            new_widget = LoopWidget()
            new_widget.setValue(old_widget.value())
            self.tree.setItemWidget(new_item, 0, new_widget)

        new_item.setExpanded(item.isExpanded())

        for i in range(item.childCount()):
            self.clone_item(item.child(i), new_item, i)

        return new_item

    def move_item(self, item, direction):

        if item is self.root_item:
            return  

        parent = item.parent() or self.tree.invisibleRootItem()
        index = parent.indexOfChild(item)

        if direction == 1:
            # +2 because insertChild inserts *before*, and the old item is still there.
            index_insertion = index + 2
            index_removal = index
        else:
            index_insertion = index - 1
            index_removal = index + 1
 
        if index_insertion < 0 or index_insertion > parent.childCount():
            return 

        new_item = self.clone_item(item, parent, index_insertion)
        parent.takeChild(index_removal)
        self.tree.setCurrentItem(new_item)

    def move_up(self):

        items = self.tree.selectedItems()
        if not items:
            return
        self.move_item(items[0], -1)

    def move_down(self):

        items = self.tree.selectedItems()
        if not items:
            return
        self.move_item(items[0], +1)

    def get_protocol(self):
        
        def traverse(item) -> Deque:

            widget = self.tree.itemWidget(item, 0)
            if widget is None:
                return deque()

            if isinstance(widget, StimWidget):
                return deque([widget.to_protocol_item()])

            elif isinstance(widget, LoopWidget):
                queue = deque()
                for i in range(item.childCount()):
                    queue.extend(traverse(item.child(i)))
                return deque(q for _ in range(widget.value()) for q in queue)

            return deque()

        return traverse(self.root_item)

    def clear_protocol(self):

        def update_item(item: QTreeWidgetItem):

            widget = self.tree.itemWidget(item, 0)
            if widget is not None:
                widget.deleteLater()
            for i in range(item.childCount()):
                update_item(item.child(i))

        update_item(self.root_item)
        self.tree.clear()

        self.root_item = QTreeWidgetItem(self.tree)
        self.tree.addTopLevelItem(self.root_item)
        self.root_widget = LoopWidget()
        self.tree.setItemWidget(self.root_item, 0, self.root_widget)

    def set_protocol(self, protocol: Deque[ProtocolItem]) -> None:
        self.clear_protocol()
        for protocol_item in protocol:
            self.add_stim_widget(protocol_item)

    def get_state(self) -> Dict:
        state = {}
        state['debouncer_length'] = self.spb_debouncer_length.value()
        state['protocol'] = self.get_protocol()
        return state

    def set_state(self, state: Dict) -> None:
        
        setters = {
            'debouncer_length': self.spb_debouncer_length.setValue,
            'protocol': self.set_protocol
        }

        for key, setter in setters.items():
            if key in state:
                setter(state[key])       

if __name__ == "__main__":

    app = QApplication([])
    window = SequencerWidget()
    window.show()
    app.exec_()

    print(window.get_protocol())
