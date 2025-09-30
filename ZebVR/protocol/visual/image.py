from ...protocol import (
    Stim, 
    ProtocolItem,
    VisualProtocolItem, 
    VisualProtocolItemWidget, 
    StopWidget, 
    Debouncer
)
from typing import Tuple, Dict
from qt_widgets import LabeledDoubleSpinBox, FileOpenLabeledEditButton
from PyQt5.QtWidgets import (
    QGroupBox, 
    QVBoxLayout,
    QApplication, 
)
from ...utils import set_from_dict
from ..default import DEFAULT
class Image(VisualProtocolItem):

    STIM_SELECT = Stim.IMAGE

    def __init__(
            self, 
            image_path: str = DEFAULT['image_path'],
            image_res_px_per_mm: float = DEFAULT['image_res_px_per_mm'],
            image_offset_mm: Tuple[float, float] = DEFAULT['image_offset_mm'],
            *args,
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)
        self.image_path = image_path
        self.image_res_px_per_mm = image_res_px_per_mm
        self.image_offset_mm = image_offset_mm

    def start(self) -> Dict:

        super().start()

        command = {
            'stim_select': self.STIM_SELECT,
            'image_path': self.image_path,
            'image_res_px_per_mm': self.image_res_px_per_mm,
            'image_offset_mm': self.image_offset_mm,
            'foreground_color': self.foreground_color,
            'background_color': self.background_color,
            'closed_loop': self.closed_loop
        }
        return command
    
class ImageWidget(VisualProtocolItemWidget):

    def __init__(
            self,
            image_path: str = DEFAULT['image_path'],
            image_res_px_per_mm: float = DEFAULT['image_res_px_per_mm'],
            image_offset_mm: Tuple[float, float] = DEFAULT['image_offset_mm'],
            *args, 
            **kwargs
        ) -> None:

        self.image_path = image_path
        self.image_res_px_per_mm = image_res_px_per_mm
        self.image_offset_mm = image_offset_mm
        
        super().__init__(*args, **kwargs)

    def declare_components(self) -> None:

        super().declare_components()

        self.fs_image_path = FileOpenLabeledEditButton()
        self.fs_image_path.setText(self.image_path)
        self.fs_image_path.textChanged.connect(self.state_changed)

        self.sb_image_res_px_per_mm = LabeledDoubleSpinBox()
        self.sb_image_res_px_per_mm.setText('resolution (pix/mm)')
        self.sb_image_res_px_per_mm.setRange(0,10_000)
        self.sb_image_res_px_per_mm.setValue(self.image_res_px_per_mm)
        self.sb_image_res_px_per_mm.valueChanged.connect(self.state_changed)

        self.sb_image_offset_mm_x = LabeledDoubleSpinBox()
        self.sb_image_offset_mm_x.setText('X (mm)')
        self.sb_image_offset_mm_x.setRange(-10_000,10_000)
        self.sb_image_offset_mm_x.setValue(self.image_offset_mm[0])
        self.sb_image_offset_mm_x.setSingleStep(0.1)
        self.sb_image_offset_mm_x.valueChanged.connect(self.state_changed)

        self.sb_image_offset_mm_y = LabeledDoubleSpinBox()
        self.sb_image_offset_mm_y.setText('Y (mm)')
        self.sb_image_offset_mm_y.setRange(-10_000,10_000)
        self.sb_image_offset_mm_y.setValue(self.image_offset_mm[1])
        self.sb_image_offset_mm_y.setSingleStep(0.1)
        self.sb_image_offset_mm_y.valueChanged.connect(self.state_changed)

    def layout_components(self) -> None:
        
        super().layout_components()

        image_layout = QVBoxLayout()
        image_layout.addWidget(self.fs_image_path)
        image_layout.addWidget(self.sb_image_res_px_per_mm)
        image_layout.addWidget(self.sb_image_offset_mm_x)
        image_layout.addWidget(self.sb_image_offset_mm_y)
        image_layout.addStretch()

        self.image_group = QGroupBox('Image parameters')
        self.image_group.setLayout(image_layout)

        self.main_layout.addWidget(self.image_group)
        self.main_layout.addWidget(self.stop_widget)

    def get_state(self) -> Dict:
        
        state = super().get_state()
        state['image_path'] = self.fs_image_path.text()
        state['image_res_px_per_mm'] = self.sb_image_res_px_per_mm.value()
        state['image_offset_mm'] = (
            self.sb_image_offset_mm_x.value(),
            self.sb_image_offset_mm_y.value()
        )
        return state
    
    def set_state(self, state: Dict) -> None:
        
        super().set_state(state)

        set_from_dict(
            dictionary = state,
            key = 'image_path',
            setter = self.fs_image_path.setText,
            default = self.image_path,
        )
        set_from_dict(
            dictionary = state,
            key = 'image_res_px_per_mm',
            setter = self.sb_image_res_px_per_mm.setValue,
            default = self.image_res_px_per_mm,
            cast = float
        )
        set_from_dict(
            dictionary = state,
            key = 'image_offset_mm',
            setter = self.sb_image_offset_mm_x.setValue,
            default = self.image_offset_mm,
            cast = lambda x: float(x[0])
        )
        set_from_dict(
            dictionary = state,
            key = 'image_offset_mm',
            setter = self.sb_image_offset_mm_y.setValue,
            default = self.image_offset_mm,
            cast = lambda x: float(x[1])
        )

    def from_protocol_item(self, protocol_item: ProtocolItem) -> None:

        super().from_protocol_item(protocol_item)

        if isinstance(protocol_item, Image):
            self.fs_image_path.setText(protocol_item.image_path)
            self.sb_image_res_px_per_mm.setValue(protocol_item.image_res_px_per_mm)
            self.sb_image_offset_mm_x.setValue(protocol_item.image_offset_mm[0])
            self.sb_image_offset_mm_y.setValue(protocol_item.image_offset_mm[1])

    def to_protocol_item(self) -> Image:
        
        foreground_color = (
            self.sb_foreground_color_R.value(), 
            self.sb_foreground_color_G.value(),
            self.sb_foreground_color_B.value(),
            self.sb_foreground_color_A.value()
        )
        background_color = (
            self.sb_background_color_R.value(), 
            self.sb_background_color_G.value(),
            self.sb_background_color_B.value(),
            self.sb_background_color_A.value()
        )
        closed_loop = self.chb_closed_loop.isChecked()

        protocol = Image(
            foreground_color = foreground_color,
            background_color = background_color,
            closed_loop = closed_loop,
            image_offset_mm = (
                self.sb_image_offset_mm_x.value(),
                self.sb_image_offset_mm_y.value()
            ),
            image_path = self.fs_image_path.text(),
            image_res_px_per_mm = self.sb_image_res_px_per_mm.value(),
            stop_condition = self.stop_widget.to_stop_condition()
        )
        return protocol
    
if __name__ == '__main__':

    app = QApplication([])
    window = ImageWidget(
        stop_widget = StopWidget(
            debouncer = Debouncer()
        )
    )
    window.show()
    app.exec()
 