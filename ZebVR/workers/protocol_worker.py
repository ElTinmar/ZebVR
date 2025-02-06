from dagline import WorkerNode
import time
from numpy.typing import NDArray
from typing import Dict, Optional, Any, Deque
from ZebVR.protocol import ProtocolItem
    
class Protocol(WorkerNode):

    def __init__(
            self, 
            protocol: Optional[Deque[ProtocolItem]] = None,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.protocol = protocol

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

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:    
        
        try:
            item = self.protocol.popleft()
        except IndexError:
            # sleep a bit to let enough time for the message 
            # to be delivered before closing the queue
            time.sleep(1)

            print('Protocol finished, stopping sequencer')
            self.stop_event.set()
            return None

        # item.run() either waits and eventually returns None, 
        # or returns a Dict with command dictionnary 
        command = item.run()

        if command is None:
            return 
        
        res = {}
        res['visual_stim_control'] = command
        return res
    
class ProtocolV2(WorkerNode):
    # Implementing triggers

    def __init__(
            self, 
            protocol: Optional[Deque[ProtocolItem]] = None,
            *args, 
            **kwargs
        ):

        super().__init__(*args, **kwargs)
        self.protocol = protocol

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

    def process_metadata(self, metadata: Dict) -> Optional[Dict]:    
        # TODO don't stop the loop with pause
        
        try:
            item = self.protocol.popleft()
        except IndexError:
            # sleep a bit to let enough time for the message 
            # to be delivered before closing the queue
            time.sleep(1)

            print('Protocol finished, stopping sequencer')
            self.stop_event.set()
            return None

        # item.run() either waits and eventually returns None, 
        # or returns a Dict with command dictionnary 
        command = item.run()

        if command is None:
            return 
        
        res = {}
        res['visual_stim_control'] = command
        return res