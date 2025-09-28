from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QTreeWidget, QTreeWidgetItem, QLineEdit, QSpinBox
)
from PyQt5.QtCore import Qt
import sys
from .protocol_widget import StimWidget
from ..protocol import ProtocolItem, Debouncer
from daq_tools import (
    BoardInfo,
    BoardType
)
import numpy as np
from numpy.typing import NDArray
from pathlib import Path
from typing import List, Dict

class MockLoopWidget(QSpinBox):

    def __init__(self):
        super().__init__()
        self.setRange(1, 100)
        self.setValue(3)


class SequencerWidget(QWidget):

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

        self.setWindowTitle("Sequencer Tree Demo")
        layout = QVBoxLayout(self)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setDragEnabled(True)
        self.tree.setAcceptDrops(True)
        self.tree.setDragDropMode(QTreeWidget.InternalMove)
        self.tree.setDefaultDropAction(Qt.MoveAction)
        self.tree.setSelectionMode(QTreeWidget.SingleSelection)
        layout.addWidget(self.tree)

        # Root loop
        self.root_item = QTreeWidgetItem(self.tree)
        self.tree.addTopLevelItem(self.root_item)
        self.root_widget = MockLoopWidget()
        self.tree.setItemWidget(self.root_item, 0, self.root_widget)
        self.tree.expandAll()

        # Buttons
        btn_add_stim = QPushButton("Add Stim")
        btn_add_loop = QPushButton("Add Loop")
        btn_remove = QPushButton("Remove Selected")
        btn_move_up = QPushButton("Move Up")
        btn_move_down = QPushButton("Move Down")
        btn_print = QPushButton("Print Protocol")

        layout.addWidget(btn_add_stim)
        layout.addWidget(btn_add_loop)
        layout.addWidget(btn_remove)
        layout.addWidget(btn_move_up)
        layout.addWidget(btn_move_down)
        layout.addWidget(btn_print)

        btn_add_stim.clicked.connect(self.add_stim)
        btn_add_loop.clicked.connect(self.add_loop)
        btn_remove.clicked.connect(self.remove_selected)
        btn_move_up.clicked.connect(self.move_up)
        btn_move_down.clicked.connect(self.move_down)
        btn_print.clicked.connect(self.print_protocol)

    def set_daq_boards(self, daq_boards: Dict[BoardType, List[BoardInfo]]):

        self.daq_boards = daq_boards
        for i in range(self.list.count()):
            item = self.list.item(i)
            stim = self.list.itemWidget(item)
            stim.blockSignals(True)
            stim.set_daq_boards(self.daq_boards)
            stim.blockSignals(False)
            
        self.state_changed.emit()

    def update_debouncer(self, value: int) -> None:
        self.debouncer.set_buffer_length(value)
        self.state_changed.emit()

    def set_background_image(self, image: NDArray) -> None:
        self.background_image = image
        for i in range(self.list.count()):
            item = self.list.item(i)
            stim = self.list.itemWidget(item)
            stim.set_background_image(image)

    # TODO check that
    def on_size_change(self):
        for i in range(self.list.count()):
            item = self.list.item(i)
            stim = self.list.itemWidget(item)
            item.setSizeHint(stim.sizeHint())

    def _selected_or_root(self):

        items = self.tree.selectedItems()
        return items[0] if items else self.root_item

    def _normalize_parent(self, parent_item):

        widget = self.tree.itemWidget(parent_item, 0)
        if isinstance(widget, StimWidget):
            return parent_item.parent() or self.root_item
        return parent_item

    def add_stim(self):

        parent_item = self._normalize_parent(self._selected_or_root())
        item = QTreeWidgetItem(parent_item)
        stim_widget = StimWidget(self.debouncer, self.daq_boards, self.background_image)
        self.tree.setItemWidget(item, 0, stim_widget)
        parent_item.setExpanded(True)

    def add_loop(self):

        parent_item = self._normalize_parent(self._selected_or_root())
        item = QTreeWidgetItem(parent_item)
        self.tree.setItemWidget(item, 0, MockLoopWidget())
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
            new_widget.set_state(old_widget.get_state())
            self.tree.setItemWidget(new_item, 0, new_widget)

        elif isinstance(old_widget, MockLoopWidget):
            new_widget = MockLoopWidget()
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

    def _traverse(self, item):

        widget = self.tree.itemWidget(item, 0)
        if widget is None: return None
        children = [self._traverse(item.child(i)) for i in range(item.childCount())]
        children = [c for c in children if c is not None]

        if isinstance(widget, StimWidget):
            return {"type": "stim", "name": widget.get_state()}
        
        elif isinstance(widget, MockLoopWidget):
            return {"type": "loop", "count": widget.value(), "body": children}

    def print_protocol(self):

        protocol = self._traverse(self.root_item)
        print(protocol)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    demo = SequencerWidget()
    demo.resize(400, 400)
    demo.show()
    sys.exit(app.exec_())
