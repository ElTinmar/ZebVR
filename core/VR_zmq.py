from core.abstractclasses import Background, Camera, Tracker, Stimulus, Projector, CameraDisplay
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
        print(f'Camera sent image {self.data.get_index()}',flush=True)

        ret = {
            'index': self.data.get_index(),
            'timestamp':  self.data.get_timestamp(),
            'frame': self.data.get_img()
        }
        return ret
    
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

    def pre_loop(self) -> None:
        self.cam_display.init_window()

    def post_loop(self) -> None:
        self.cam_display.close_window()
        print(f'{self.name}: recv {1e-9 * self.recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_recv {1e-9 * self.post_recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: send {1e-9 * self.send_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_send {1e-9 * self.post_send_time_ns/self.num_loops} s per loop')

    def post_send(self) -> None:
        pass

    def post_recv(self, args: Any) -> Any:
        timestamp = args[0]['timestamp']
        index = args[0]['index']
        image = args[0]['frame']
    
        self.cam_display.display(image)

        print(f'{self.name} received image {index}, timestamp {timestamp}',flush=True)

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
        timestamp = args[0]['timestamp']
        index = args[0]['index']
        image = args[0]['frame']

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
        self.image = None
        self.name = name

    def pre_loop(self) -> None:
        cv2.namedWindow(self.name)

    def post_loop(self) -> None:
        cv2.destroyWindow(self.name)
        print(f'{self.name}: recv {1e-9 * self.recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_recv {1e-9 * self.post_recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: send {1e-9 * self.send_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_send {1e-9 * self.post_send_time_ns/self.num_loops} s per loop')

    def post_send(self) -> None:
        if self.overlay is not None:
            for c in range(self.overlay.shape[2]):
                self.overlay[:,:,c] = self.overlay[:,:,c] + self.image
            cv2.imshow(self.name, self.overlay)
            cv2.waitKey(1)

    def post_recv(self, args: Any) -> Any:
        timestamp = args[0]['timestamp']
        index = args[0]['index']
        image = args[0]['frame']

        tracking = self.tracker.track(image)
        self.overlay = self.tracker.tracking_overlay(image)
        self.image = image 
        print(f'{self.name} received image {index}, timestamp {timestamp}',flush=True)
        
        ret = {
            'index': index,
            'timestamp': timestamp,
            'tracking': tracking
        }
        return ret
    
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
        index = args[0]['index']
        timestamp = args[0]['timestamp']
        tracking = args[0]['tracking']
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

    def pre_loop(self) -> None:
        self.projector.init_window()

    def post_loop(self) -> None:
        self.projector.close_window()
        print(f'{self.name}: recv {1e-9 * self.recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_recv {1e-9 * self.post_recv_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: send {1e-9 * self.send_time_ns/self.num_loops} s per loop')
        print(f'{self.name}: post_send {1e-9 * self.post_send_time_ns/self.num_loops} s per loop')

    def post_send(self) -> None:
        pass

    def post_recv(self, args: Any) -> Any:
        timestamp = args[0]['timestamp']
        index = args[0]['index']
        image = args[0]['frame']
        print(f'{self.name} received image {index}, timestamp {timestamp}',flush=True)
        if image is not None:
            self.projector.project(image)
