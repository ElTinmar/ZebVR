import time
from dagline import WorkerNode
from numpy.typing import NDArray
from typing import Dict, Optional
from PyQt5.QtWidgets import QApplication
from ..widgets import TrackerWidget
from pathlib import Path
from typing import Union

class TrackerGui(WorkerNode):

    def __init__(
            self,
            n_animals: int,
            settings_file: Union[Path, str] = Path('tracking.json'),
            *args,
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.n_animals = n_animals 
        self.settings_file = Path(settings_file)

    def initialize(self) -> None:
        super().initialize()
        
        self.app = QApplication([])
        self.window = TrackerWidget(
            settings_file = self.settings_file,
            n_animals = self.n_animals
        )
        self.window.show()

    def process_data(self, data: None) -> NDArray:
        self.app.processEvents()
        self.app.sendPostedEvents()
        time.sleep(0.01)

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:
        # send tracking controls
        if self.window.is_updated():
            
            state = self.window.get_state()
            res = {}
            if state['apply_to_all']:
                for i in range(self.n_animals):
                    res[f'tracker_control_{i}'] = state['substate'][i]
            else:
                id = state['animal_identity']
                res[f'tracker_control_{id}'] = state['substate'][id]

            self.window.set_updated(False)
            return res
