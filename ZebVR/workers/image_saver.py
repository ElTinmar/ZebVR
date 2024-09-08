from dagline import WorkerNode
import numpy as np
from numpy.typing import NDArray
from typing import Any
import cv2
import os
import time

#TODO: check zarr, maybe try cv2.imwrite

class ImageSaverWorker(WorkerNode):

    def __init__(
            self, 
            folder: str, 
            fps: int = 10,
            zero_padding: int = 8, 
            resize: float = 0.25,
            compress: bool = False, 
            *args, 
            **kwargs
        ):
        super().__init__(*args, **kwargs)
        self.folder = folder
        self.fps = fps
        self.resize = resize
        self.zero_padding = zero_padding
        self.compress = compress
        self.prev_time = 0

    def initialize(self) -> None:
        super().initialize()
        if not os.path.exists(self.folder):
            os.mkdir(self.folder)

    def process_data(self, data: NDArray) -> None:

        if data is not None:

            if time.monotonic() - self.prev_time > 1/self.fps:
                
                image_resized = cv2.resize(data['image'],None,None,self.resize,self.resize,cv2.INTER_NEAREST)
                metadata = data[['index','timestamp']]
                filename = os.path.join(self.folder, f"{data['index']:0{self.zero_padding}}")
                if self.compress:
                    np.savez_compressed(filename, image=image_resized, metadata=metadata)
                else:
                    np.savez(filename, image=image_resized, metadata=metadata)

                self.prev_time = time.monotonic()

    def process_metadata(self, metadata) -> Any:
        pass