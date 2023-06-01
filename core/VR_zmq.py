from core.abstractclasses import Background, Camera, Tracker, Stimulus, Projector
from parallel.dag import ZMQDataProcessingNode
from typing import Any
import cv2

class ProjectorZMQ(ZMQDataProcessingNode):
    def __init__(
            self, 
            projector : Projector,
            recv_timeout_s: int = 1
        ) -> None:
        
        super().__init__(recv_timeout_s)
        self.projector = projector

    def pre_loop(self) -> None:
        self.projector.init_window()

    def post_loop(self) -> None:
        self.projector.close_window()
        print(f'ProjectorZMQ {self.execution_time/self.num_loops} s per loop')

    def post_send(self) -> None:
        pass

    def post_recv(self, args: Any) -> Any:
        timestamp = args[0][0]
        image = args[0][1]
        print(f'Projector received tracking {timestamp}',flush=True)
        if image is not None:
            self.projector.project(image)

class CameraZMQ(ZMQDataProcessingNode):
    def __init__(
            self, 
            camera: Camera,
            recv_timeout_s: int = 1
        ) -> None:
        
        super().__init__(recv_timeout_s)
        
        self.camera = camera
        self.data = None

    def pre_loop(self) -> None:
        pass

    def post_loop(self) -> None:
        print(f'CameraZMQ {self.execution_time/self.num_loops} s per loop')

    def post_send(self) -> None:
        if self.data is not None:
            self.data.reallocate()

    def post_recv(self, args: Any) -> Any:
        self.data, res = self.camera.fetch()
        print(f'Camera sent image {self.data.get_timestamp()}',flush=True)
        return [self.data.get_timestamp(), self.data.get_img()] 
    
class BackgroundZMQ(ZMQDataProcessingNode):
    def __init__(
            self,
            background: Background,
            recv_timeout_s=1
        ) -> None:

        super().__init__(recv_timeout_s)

        self.background = background

    def pre_loop(self) -> None:
        self.background.start()

    def post_loop(self) -> None:
        self.background.stop()
        print(f'BackgroundZMQ {self.execution_time/self.num_loops} s per loop')

    def post_send(self) -> None:
        pass

    def post_recv(self, args: Any) -> Any:
        timestamp = args[0][0]
        image = args[0][1]
        self.background.add_image(image)
        print(f'Bckg received image {timestamp}' ,flush=True)
        return [timestamp, abs(image - self.background.get_background())]
    
class TrackerZMQ(ZMQDataProcessingNode):
    def __init__(
            self, 
            name: str,
            tracker: Tracker,
            recv_timeout_s=1
        ) -> None:

        super().__init__(recv_timeout_s)
        self.tracker = tracker
        self.overlay = None
        self.image = None
        self.name = name

    def pre_loop(self) -> None:
        cv2.namedWindow(self.name)

    def post_loop(self) -> None:
        cv2.destroyWindow(self.name)
        print(f'TrackerZMQ {self.execution_time/self.num_loops} s per loop')
    
    def post_send(self) -> None:
        if self.overlay is not None:
            for c in range(self.overlay.shape[2]):
                self.overlay[:,:,c] = self.overlay[:,:,c] + self.image
            cv2.imshow(self.name, self.overlay)
            cv2.waitKey(1)

    def post_recv(self, args: Any) -> Any:
        timestamp = args[0][0]
        image = args[0][1]
        tracking = self.tracker.track(image)
        self.overlay = self.tracker.tracking_overlay(image)
        self.image = image 
        print(f'{self.name} received image {timestamp}',flush=True)
        return [timestamp, tracking]
    
class StimulusZMQ(ZMQDataProcessingNode):
    def __init__(
            self, 
            stimulus: Stimulus,
            recv_timeout_s: int = 1
        ) -> None:
        
        super().__init__(recv_timeout_s)
        
        self.stimulus = stimulus

    def pre_loop(self) -> None:
        pass

    def post_loop(self) -> None:
        print(f'StimulusZMQ {self.execution_time/self.num_loops} s per loop')

    def post_send(self) -> None:
        pass

    def post_recv(self, args: Any) -> Any:
        timestamp = args[0][0]
        tracking = args[0][1]
        print(f'Stimulus received tracking {timestamp}',flush=True)
        image = self.stimulus.create_stim_image(timestamp, tracking)
        return [timestamp, image]
    
