from dagline import WorkerNode
import numpy as np
from numpy.typing import NDArray
from typing import Any
import cv2
import os

#TODO: check zarr, maybe try cv2.imwrite

class ImageSaverWorker(WorkerNode):

    def __init__(self, folder: str, zero_padding: int = 8, compress: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.folder = folder
        self.zero_padding = zero_padding
        self.compress = compress

    def initialize(self) -> None:
        super().initialize()
        if not os.path.exists(self.folder):
            os.mkdir(self.folder)

    def process_data(self, data: NDArray) -> None:
        if data is not None:
            index, timestamp, image = data
            image_resized = cv2.resize(image,None,None,0.25,0.25,cv2.INTER_NEAREST)
            metadata = np.array( 
                (index, timestamp), 
                dtype = np.dtype([('index',np.int64), ('timestamp',np.float32)]) 
            )
            filename = os.path.join(self.folder, f'{index:0{self.zero_padding}}')
            if self.compress:
                np.savez_compressed(filename, image=image_resized, metadata=metadata)
            else:
                np.savez(filename, image=image_resized, metadata=metadata)

    def process_metadata(self, metadata) -> Any:
        pass