import json
from dagline import WorkerNode
from ZebVR.utils import append_timestamp_to_filename

class TrackingSaver(WorkerNode):

    def __init__(
            self, 
            filename: str = 'stimulus.json',
            *args, 
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.filename = filename
        self.fd = None

    def set_filename(self, filename:str):
        self.filename = filename

    def initialize(self):

        super().initialize()
        
        file = append_timestamp_to_filename(self.filename)
        self.fd = open(file, 'w')

    def cleanup(self):
        super().cleanup()
        if self.fd is not None:
            self.fd.close()

    def process_data(self, data) -> None:
        pass
        
    def process_metadata(self, metadata) -> None:

        if self.fd is None:
            return
        
        if metadata is None:
            return

        json.dump(metadata, self.fd)
        self.fd.write('\n')