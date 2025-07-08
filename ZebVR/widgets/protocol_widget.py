from typing import Dict, Optional, List
from numpy.typing import NDArray
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, 
    QStackedWidget, 
    QVBoxLayout, 
    QComboBox,
)
from ZebVR.protocol import (
    Debouncer,
    Stim,
    ProtocolItem,
    StopWidget,
    PROTOCOL_WIDGETS,
    DAQ_ProtocolItemWidget
)
from daq_tools import (
    BoardInfo,
    BoardType
)

class StimWidget(QWidget):

    state_changed = pyqtSignal()
    size_changed = pyqtSignal()

    def __init__(
            self, 
            debouncer: Debouncer,
            daq_boards: Dict[BoardType, List[BoardInfo]] = {},
            background_image: Optional[NDArray] = None,
            *args, 
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        
        self.debouncer = debouncer
        self.background_image = background_image
        self.updated = False
        self.protocol_item_widgets = []
        self.daq_boards = daq_boards

        self.setWindowTitle('Stimulus controls')

        self.declare_components()
        self.layout_components()
        self.stim_changed()
    
    def declare_components(self) -> None:
    
        self.cmb_stim_select = QComboBox()

        for constructor, stim_type in PROTOCOL_WIDGETS:
            if issubclass(constructor, DAQ_ProtocolItemWidget):
                if self.daq_boards:
                    widget = constructor(
                        boards = self.daq_boards,
                        stop_widget = StopWidget(self.debouncer, self.background_image)
                    )
                else:
                    continue
            else:
                widget = constructor(stop_widget = StopWidget(self.debouncer, self.background_image))
            
            self.cmb_stim_select.addItem(str(stim_type))
            widget.state_changed.connect(self.on_change)
            self.protocol_item_widgets.append(widget)
        
        self.cmb_stim_select.currentIndexChanged.connect(self.stim_changed)


    def layout_components(self) -> None:

        self.stack = QStackedWidget()
        for widget in self.protocol_item_widgets:
            self.stack.addWidget(widget) 

        layout = QVBoxLayout(self)
        layout.addWidget(self.cmb_stim_select)
        layout.addWidget(self.stack)
        layout.addStretch()

    def on_size_changed(self):
        self.adjustSize() 
        self.size_changed.emit()

    def set_daq_boards(self, daq_boards: Dict[BoardType, List[BoardInfo]]):

        self.daq_boards = daq_boards

        # reset everything
        current_stim = self.cmb_stim_select.currentText()
        self.cmb_stim_select.clear()
        
        while self.stack.count():
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.setParent(None)
            widget.deleteLater()

        self.protocol_item_widgets.clear()

        # Rebuild protocol item widgets
        for constructor, stim_type in PROTOCOL_WIDGETS:
            if issubclass(constructor, DAQ_ProtocolItemWidget):
                if self.daq_boards:
                    widget = constructor(
                        boards=self.daq_boards,
                        stop_widget=StopWidget(self.debouncer, self.background_image)
                    )
                else: 
                    continue
            else:
                widget = constructor(
                    stop_widget=StopWidget(self.debouncer, self.background_image)
                )

            self.cmb_stim_select.addItem(str(stim_type))
            widget.state_changed.connect(self.on_change)
            self.protocol_item_widgets.append(widget)
            self.stack.addWidget(widget)

        # Reset combobox
        self.cmb_stim_select.setCurrentText(current_stim)
        self.stim_changed()
        
    def set_background_image(self, image: NDArray) -> None:
        self.background_image = image
        current_widget = self.stack.currentWidget()
        current_widget.stop_widget.set_background_image(image)

    def stim_changed(self):
        self.stack.setCurrentIndex(self.cmb_stim_select.currentIndex())
        current_widget = self.stack.currentWidget()
        if current_widget:
            new_height = current_widget.sizeHint().height()  
            self.stack.setFixedHeight(new_height)
            self.adjustSize() 
        self.size_changed.emit()
        self.on_change()

    def on_change(self):
        self.updated = True
        self.state_changed.emit()

    def is_updated(self) -> bool:
        return self.updated
    
    def set_updated(self, updated:bool) -> None:
        self.updated = updated

    def get_state(self) -> Dict:
        state = {}
        state['stim_select'] = PROTOCOL_WIDGETS[self.cmb_stim_select.currentIndex()][1]
        current_widget = self.stack.currentWidget()
        state.update(current_widget.get_state())
        return state

    def set_state(self, state: Dict) -> None:
        stim_idx = state.get('stim_select', Stim.DARK)
        for i, (_, stim) in enumerate(PROTOCOL_WIDGETS):
            if stim == stim_idx:
                self.cmb_stim_select.setCurrentIndex(i)
                break

        current_widget = self.stack.currentWidget()
        current_widget.set_state(state)

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:
        self.cmb_stim_select.setCurrentIndex(protocol_item.STIM_SELECT) 
        current_widget = self.stack.currentWidget()
        current_widget.from_protocol_item(protocol_item)

    def to_protocol_item(self) -> ProtocolItem:
        current_widget = self.stack.currentWidget()
        return current_widget.to_protocol_item()
    