from dagline import WorkerNode
import time
from numpy.typing import NDArray
from typing import Dict, Optional, Any, Deque
from ..protocol import ProtocolItem

class Protocol(WorkerNode):

    def __init__(
            self, 
            protocol: Optional[Deque[ProtocolItem]] = None,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.protocol = protocol
        self.current_item = None

    def set_protocol(self, protocol: Deque[ProtocolItem]) -> None:
        self.protocol = protocol

    def initialize(self) -> None:
        super().initialize()
        for protocol_item in self.protocol:
            protocol_item.initialize()

    def cleanup(self) -> None:
        super().cleanup()
        for protocol_item in self.protocol:
            protocol_item.cleanup()

    def process_data(self, data: Any) -> NDArray:
        pass

    def next(self):

        command = None
        try:
            self.current_item = self.protocol.popleft()
            command = self.current_item.start()

        except IndexError:
            # sleep a bit to let enough time for the message 
            # to be delivered before closing the queue
            time.sleep(1)

            print('Protocol finished, stopping sequencer')
            self.stop_event.set()
            return None

        return command

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:    

        if self.current_item is not None:
            if not self.current_item.done(metadata):
                # prevent spamming worker logger (otherwise logger queue gets full -> OOM)
                # sleep needs to be small enough to keep up with metadata, but big enough
                # to not fill the logger queue.
                # TODO: find a real solution
                time.sleep(0.002) 
                return
        
        command = self.next()
        if command is None:
            return 
        
        res = {}
        res['stim_control'] = command
        res['audio_stim_control'] = command
        return res