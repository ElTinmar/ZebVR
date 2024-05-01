from dagline import WorkerNode
from PyQt5.QtWidgets import QApplication, QWidget
from multiprocessing import Process

class QtWorker(WorkerNode):

    def __init__(self, widget: QWidget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget = widget 
        self.gui_process = None

    def run(self) -> None:
        app = QApplication()
        self.widget.show()
        while not self.stop_event.is_set():
            app.processEvents()

    def initialize(self) -> None:
        super().initialize()
        # launch main window loop in a separate process 
        self.gui_process = Process(target=self.run)
        self.gui_process.start()

    def cleanup(self) -> None:
        self.gui_process.join()