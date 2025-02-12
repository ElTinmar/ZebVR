from dagline import WorkerNode
import time
from numpy.typing import NDArray
from typing import Dict, Optional, Any, Deque
from ..protocol import ProtocolItem
    

class Protocol(WorkerNode):
    # Implementing triggers

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

        self.current_item = self.protocol.popleft()
        self.current_item.start()

    def cleanup(self) -> None:
        super().cleanup()
        for protocol_item in self.protocol:
            protocol_item.cleanup()

    def process_data(self, data: Any) -> NDArray:
        pass

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:    

        command, done = self.current_item.done(metadata)

        if not done:
            return
        
        try:
            self.current_item = self.protocol.popleft()
            self.current_item.start()

        except IndexError:
            # sleep a bit to let enough time for the message 
            # to be delivered before closing the queue
            time.sleep(1)

            print('Protocol finished, stopping sequencer')
            self.stop_event.set()
            # TODO maybe add handle to parent dag to ask nicely to stop everyone
            return None

        if command is None:
            return 
        
        res = {}
        res['visual_stim_control'] = command
        return res