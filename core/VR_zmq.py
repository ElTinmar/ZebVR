from core.abstractclasses import Background, Camera, Tracker, Stimulus, Projector, CameraDisplay, TrackerDisplay
from parallel.zmq_worker import ZMQDataProcessingNode, ZMQSocketInfo
from typing import Any
import cv2
from typing import List

class CameraZMQ(ZMQDataProcessingNode):
    def __init__(
            self, 
            camera: Camera,
            input_info : List[ZMQSocketInfo],
            output_info : List[ZMQSocketInfo],
            recv_timeout_s: int = 10,
            name: str = 'CameraZMQ' 
        ) -> None:
        
        super().__init__(input_info,output_info,recv_timeout_s)
        
        self.camera = camera
        self.data = None
        self.name = name

    def pre_loop(self) -> None:
        pass

    def post_loop(self) -> None:
        print(f'{self.name}: recv {1e-9 * self.recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_recv {1e-9 * self.post_recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: send {1e-9 * self.send_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_send {1e-9 * self.post_send_time_ns/self.num_loops} s per loop')

    def post_send(self) -> None:
        if self.data is not None:
            self.data.reallocate()

    def post_recv(self, args: Any) -> Any:
        self.data, res = self.camera.fetch()
        if res:
            print(f'Camera sent image {self.data.get_index()}',flush=True)

            ret = {
                'index': self.data.get_index(),
                'timestamp':  self.data.get_timestamp(),
                'frame': self.data.get_img()
            }
            return ret
        else:
            return None
    
class CameraDisplayZMQ(ZMQDataProcessingNode):
    def __init__(
            self, 
            cam_display: CameraDisplay, 
            input_info : List[ZMQSocketInfo],
            output_info : List[ZMQSocketInfo],
            recv_timeout_s: int = 10,
            name: str = 'CameraDisplayZMQ' 
        ) -> None:
        
        super().__init__(input_info,output_info,recv_timeout_s)
        self.name = name
        self.cam_display = cam_display
        self.last_frame = 0
        self.discarded_frames = []

    def pre_loop(self) -> None:
        self.cam_display.init_window()

    def post_loop(self) -> None:
        self.cam_display.close_window()
        print(f'{self.name}: recv {1e-9 * self.recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_recv {1e-9 * self.post_recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: send {1e-9 * self.send_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_send {1e-9 * self.post_send_time_ns/self.num_loops} s per loop')
        print(f'discarded {len(self.discarded_frames)} frames')
        
    def post_send(self) -> None:
        pass

    def post_recv(self, args: Any) -> Any:
        timestamp = args['timestamp']
        index = args['index']
        image = args['frame']
        if index > self.last_frame:
            self.cam_display.display(image)
            print(f'{self.name} received image {index}, timestamp {timestamp}',flush=True)
            self.last_frame = index
        else:
            self.discarded_frames.append(index)

class BackgroundZMQ(ZMQDataProcessingNode):
    def __init__(
            self,
            background: Background,
            input_info : List[ZMQSocketInfo],
            output_info : List[ZMQSocketInfo],
            recv_timeout_s: int = 10,
            name: str = 'BackgroundZMQ' 
        ) -> None:

        super().__init__(input_info,output_info,recv_timeout_s)

        self.background = background
        self.name = name

    def pre_loop(self) -> None:
        self.background.start()

    def post_loop(self) -> None:
        self.background.stop()
        print(f'{self.name}: recv {1e-9 * self.recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_recv {1e-9 * self.post_recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: send {1e-9 * self.send_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_send {1e-9 * self.post_send_time_ns/self.num_loops} s per loop')

    def post_send(self) -> None:
        pass

    def post_recv(self, args: Any) -> Any:
        timestamp = args['timestamp']
        index = args['index']
        image = args['frame']

        self.background.add_image(image)
        print(f'{self.name} received image {index}, timestamp {timestamp}',flush=True)

        ret = {
            'index': index,
            'timestamp':  timestamp,
            'frame': -1.0*(image - self.background.get_background())
        }
        return ret
    
class TrackerZMQ(ZMQDataProcessingNode):
    def __init__(
            self, 
            name: str,
            tracker: Tracker,
            input_info : List[ZMQSocketInfo],
            output_info : List[ZMQSocketInfo],
            recv_timeout_s: int = 10
        ) -> None:

        super().__init__(input_info,output_info,recv_timeout_s)

        self.tracker = tracker
        self.overlay = None
        self.name = name

    def pre_loop(self) -> None:
        pass

    def post_loop(self) -> None:
        print(f'{self.name}: recv {1e-9 * self.recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_recv {1e-9 * self.post_recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: send {1e-9 * self.send_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_send {1e-9 * self.post_send_time_ns/self.num_loops} s per loop')

    def post_send(self) -> None:
        pass

    def post_recv(self, args: Any) -> Any:
        timestamp = args['timestamp']
        index = args['index']
        image = args['frame']

        tracking = self.tracker.track(image)
        print(f'{self.name} received image {index}, timestamp {timestamp}',flush=True)
        
        ret = {
            'index': index,
            'timestamp': timestamp,
            'tracking': tracking,
            'frame': image
        }
        return ret
    
class TrackerDisplayZMQ(ZMQDataProcessingNode):
    def __init__(
            self, 
            track_display: TrackerDisplay, 
            input_info : List[ZMQSocketInfo],
            output_info : List[ZMQSocketInfo],
            recv_timeout_s: int = 10,
            name: str = 'TrackerDisplayZMQ' 
        ) -> None:
        
        super().__init__(input_info,output_info,recv_timeout_s)
        self.name = name
        self.track_display = track_display
        self.last_frame = 0
        self.discarded_frames = []

    def pre_loop(self) -> None:
        self.track_display.init_window()

    def post_loop(self) -> None:
        self.track_display.close_window()
        print(f'{self.name}: recv {1e-9 * self.recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_recv {1e-9 * self.post_recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: send {1e-9 * self.send_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_send {1e-9 * self.post_send_time_ns/self.num_loops} s per loop')
        print(f'discarded {len(self.discarded_frames)} frames')

    def post_send(self) -> None:
        pass

    def post_recv(self, args: Any) -> Any:
        timestamp = args['timestamp']
        index = args['index']
        image = args['frame']
        tracking = args['tracking']
    
        if index > self.last_frame:
            self.track_display.display(tracking, image)
            print(f'{self.name} received image {index}, timestamp {timestamp}',flush=True)
            self.last_frame = index
        else:
            self.discarded_frames.append(index)

class StimulusZMQ(ZMQDataProcessingNode):
    def __init__(
            self, 
            stimulus: Stimulus,
            input_info : List[ZMQSocketInfo],
            output_info : List[ZMQSocketInfo],
            recv_timeout_s: int = 10,
            name: str = 'StimulusZMQ' 
        ) -> None:
        
        super().__init__(input_info,output_info,recv_timeout_s)
        
        self.stimulus = stimulus
        self.name = name

    def pre_loop(self) -> None:
        pass

    def post_loop(self) -> None:
        print(f'{self.name}: recv {1e-9 * self.recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_recv {1e-9 * self.post_recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: send {1e-9 * self.send_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_send {1e-9 * self.post_send_time_ns/self.num_loops} s per loop')
        
    def post_send(self) -> None:
        pass

    def post_recv(self, args: Any) -> Any:
        index = args['index']
        timestamp = args['timestamp']
        tracking = args['tracking']
        print(f'{self.name} received image {index}, timestamp {timestamp}',flush=True)

        ret = {
            'index': index,
            'timestamp':  timestamp,
            'frame': self.stimulus.create_stim_image(timestamp, tracking)
        }
        return ret
    
class ProjectorZMQ(ZMQDataProcessingNode):
    def __init__(
            self, 
            projector : Projector,
            input_info : List[ZMQSocketInfo],
            output_info : List[ZMQSocketInfo],
            recv_timeout_s: int = 10,
            name: str = 'ProjectorZMQ' 
        ) -> None:
        
        super().__init__(input_info,output_info,recv_timeout_s)
        self.projector = projector
        self.name = name
        self.last_frame = 0
        self.discarded_frames = []

    def pre_loop(self) -> None:
        self.projector.init_window()

    def post_loop(self) -> None:
        self.projector.close_window()
        print(f'{self.name}: recv {1e-9 * self.recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_recv {1e-9 * self.post_recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: send {1e-9 * self.send_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_send {1e-9 * self.post_send_time_ns/self.num_loops} s per loop')
        print(f'discarded {len(self.discarded_frames)} frames')

    def post_send(self) -> None:
        pass

    def post_recv(self, args: Any) -> Any:
        timestamp = args['timestamp']
        index = args['index']
        image = args['frame']
        if index > self.last_frame:
            print(f'{self.name} received image {index}, timestamp {timestamp}',flush=True)
            if image is not None:
                self.projector.project(image)
            self.last_frame = index
        else:
            self.discarded_frames.append(index)
