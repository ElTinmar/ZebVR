from multiprocessing import set_start_method
import os
os.environ["OMP_NUM_THREADS"] = "1"
from PyQt5.QtWidgets import QApplication
from ZebVR.gui import MainGui

if __name__ == "__main__":

    set_start_method('spawn')

    app = QApplication([])
    main = MainGui()
    main.show()
    app.exec_()
