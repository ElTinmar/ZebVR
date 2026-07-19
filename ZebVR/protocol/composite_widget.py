from typing import Dict, Tuple, List, Type
from .stop_condition import StopWidget
from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
    QWidget, 
    QVBoxLayout,
    QPushButton,
    QSizePolicy,
    QMenu,
    QTabWidget
)
from .stim import Stim
from .protocol_item import CompositeProtocolItem, ProtocolItemWidget

class AddButtonTabWidget(QTabWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabsClosable(True)
        
        self.setStyleSheet("""
            QTabBar::tab:disabled {
                background: transparent;
                border: none;
                width: 35px; /* Give the dropdown menu button breathing room */
            }
            QTabBar QPushButton {
                background: transparent;
                border: none;
                font-size: 24px;
                padding-bottom: 2px;
            }
            QTabBar QPushButton::menu-indicator {
                image: none; /* Hide the default tiny down-arrow if desired */
            }
            QTabBar QPushButton:hover {
                color: #0078d7;
            }
        """)

        self.add_button = QPushButton("+", self)
        self.add_button.setFixedWidth(48)
        
        # 3. Append the invisible placeholder tab slot
        self.addTab(QWidget(), "")
        self.plus_index = self.count() - 1
        self.setTabEnabled(self.plus_index, False)
        
        # 4. Dock the button into the placeholder tab
        self.tabBar().setTabButton(self.plus_index, self.tabBar().LeftSide, self.add_button)
        
        # Try wiping default right-side close indicators from the plus tab
        try:
            self.tabBar().setTabButton(self.plus_index, self.tabBar().RightSide, None)
        except Exception:
            pass

    def set_menu(self, menu: QMenu):
        self.add_button.setMenu(menu)

    def insert_real_tab(self, widget: QWidget, title: str) -> int:
        target_index = self.count() - 1
        if target_index < 0:
            target_index = 0
            
        new_index = self.insertTab(target_index, widget, title)
        return new_index

    def is_plus_tab(self, index: int) -> bool:
        return index == self.count() - 1
    


class CompositeProtocolItemWidget(ProtocolItemWidget):
    
    item_added = Signal(QWidget) 

    def __init__(self, stop_widget: StopWidget, *args, **kwargs):
        super().__init__(stop_widget, *args, **kwargs)

        self.sub_widgets: List[Tuple[Stim, ProtocolItemWidget]] = []
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        self.stim_to_widget = {}
        self.widget_to_stim = {}

    def set_registry(self, stim_to_widget: dict, widget_to_stim: dict):
        self.stim_to_widget = stim_to_widget
        self.widget_to_stim = widget_to_stim
        self._update_add_menu()

    def declare_components(self) -> None:
        super().declare_components()
        
        # Use our clean custom component
        self.tabs = AddButtonTabWidget(self)
        self.tabs.tabCloseRequested.connect(self._on_tab_close_requested)
        
        # Generate the context menu and pass it into the tab bar button
        self.add_menu = QMenu(self)
        self.tabs.set_menu(self.add_menu)

    def _update_add_menu(self) -> None:
        self.add_menu.clear()
        for widget_cls, stim_enum in self.widget_to_stim.items():                
            action = self.add_menu.addAction(str(stim_enum))
            action.triggered.connect(lambda checked=False, cls=widget_cls, stim=stim_enum: self.add_item(cls, stim))

    def layout_components(self) -> None:
        self.main_layout = QVBoxLayout(self)        
        self.main_layout.addWidget(self.stim_name)
        self.main_layout.addWidget(self.tabs)
        self.main_layout.addWidget(self.stop_widget)

    def _on_tab_close_requested(self, index: int) -> None:
        if self.tabs.is_plus_tab(index):
            return

        widget = self.tabs.widget(index)
        matching_pair = next((pair for pair in self.sub_widgets if pair[1] == widget), None)
        if matching_pair:
            self.sub_widgets.remove(matching_pair)

        self.tabs.removeTab(index)
        widget.setParent(None)
        widget.deleteLater()
        
        self._refresh_tab_titles()
        self.state_changed.emit()

    def clear(self):
        while self.sub_widgets:
            self._on_tab_close_requested(0)
        self.sub_widgets = []

    def _refresh_tab_titles(self) -> None:
        loop_limit = self.tabs.count() - 1
        for i in range(loop_limit):
            current_title = self.tabs.tabText(i)
            if ":" in current_title:
                suffix = current_title.split(":", 1)[1]
                self.tabs.setTabText(i, f"{i + 1}:{suffix}")

    def add_item(self, widget_cls: Type[ProtocolItemWidget], stim: Stim) -> None:
        new_stop_widget = StopWidget(
            debouncer=self.stop_widget.debouncer,
            background_image=self.stop_widget.background_image
        )
        
        new_widget = widget_cls(stop_widget=new_stop_widget)
        new_widget.stop_widget.hide()
        new_widget.state_changed.connect(self.state_changed) 
        self.sub_widgets.append((stim, new_widget)) 

        # tab
        tab_title = f"{len(self.sub_widgets)}: {stim}"
        new_index = self.tabs.insert_real_tab(new_widget, tab_title)
        self.tabs.setCurrentIndex(new_index)          
        
        self.state_changed.emit()
        self.item_added.emit(new_widget)

    def to_protocol_item(self) -> CompositeProtocolItem:
        sub_protocols = [widget.to_protocol_item() for stim, widget in self.sub_widgets]
        return CompositeProtocolItem(
            sub_protocols=sub_protocols,
            **self._get_protocol_kwargs()
        )
    
    def get_state(self) -> Dict:
        state = super().get_state()
        state['sub_commands'] = []
        for stim, widget in self.sub_widgets:
            sub_state = {'stim_select': stim}
            sub_state.update(widget.get_state())
            state['sub_commands'].append(sub_state)
        return state
    
    def set_state(self, state: Dict) -> None:
        self.clear()

        super().set_state(state)
        sub_commands = state.get('sub_commands', [])
        for command in sub_commands:
            stim = command.get('stim_select', None)
            try:
                widget_cls = self.stim_to_widget[stim]
                self.add_item(widget_cls, stim)
                _, new_widget = self.sub_widgets[-1]
                new_widget.set_state(command)
            except:
                pass
