from core.abstractclasses import (
    Background, Camera, Tracker, Stimulus, 
    Projector, CameraDisplay, TrackerDisplay, 
    ImageSaver, DataPlotter
)
from parallel.srb_worker import DataProcessingNode
from parallel.shared_ring_buffer import DataDispatcher
from typing import Any

class Camera(DataProcessingNode):
    def __init__(
            self, 
            camera: Camera,
            input : DataDispatcher,
            output : DataDispatcher,
            recv_timeout_s: int = 10,
            name: str = 'Camera' 
        ) -> None:
        
        super().__init__(input,output,recv_timeout_s)
        
        self.camera = camera
        self.data = None
        self.name = name

    def pre_loop(self) -> None:
        self.camera.start_acquisition()

    def post_loop(self) -> None:
        self.camera.stop_acquisition()

    def post_send(self) -> None:
        if self.data is not None:
            self.data.reallocate()

    def post_recv(self, args: Any) -> Any:
        self.data, res = self.camera.fetch()
        if res:
            print(f'Camera sent image {self.data.get_index()}',flush=True)
            ret = (self.data.get_index(),
                self.data.get_timestamp(),
                self.data.get_img()
            )
            return ret
        else:
            self.stop_loop.set()
            return None
    
class CameraDisplay(DataProcessingNode):
    def __init__(
            self, 
            cam_display: CameraDisplay, 
            input : DataDispatcher,
            output : DataDispatcher,
            recv_timeout_s: int = 10,
            name: str = 'CameraDisplay' 
        ) -> None:
        
        super().__init__(input,output,recv_timeout_s)
        self.name = name
        self.cam_display = cam_display
        self.last_frame = 0
        self.discarded_frames = []

    def pre_loop(self) -> None:
        self.cam_display.init_window()

    def post_loop(self) -> None:
        super().post_loop()
        self.cam_display.close_window()
        print(f'discarded {len(self.discarded_frames)} frames')
        
    def post_recv(self, args: Any) -> Any:
        timestamp, index, image = args
        if index > self.last_frame:
            self.cam_display.display(image)
            print(f'{self.name} received image {index}, timestamp {timestamp}',flush=True)
            self.last_frame = index
        else:
            self.discarded_frames.append(index)

class Background(DataProcessingNode):
    def __init__(
            self,
            background: Background,
            input : DataDispatcher,
            output : DataDispatcher,
            recv_timeout_s: int = 10,
            name: str = 'Background',
        ) -> None:

        super().__init__(input,output,recv_timeout_s)

        self.background = background
        self.name = name

    def pre_loop(self) -> None:
        self.background.start()

    def post_loop(self) -> None:
        super().post_loop()
        self.background.stop()

    def post_recv(self, args: Any) -> Any:
        timestamp, index, image = args
        self.background.add_image(image)
        print(f'{self.name} received image {index}, timestamp {timestamp}',flush=True)
        ret = (index,timestamp, self.background.get_polarity()*(image - self.background.get_background()))
        return ret
    
class Tracker(DataProcessingNode):
    def __init__(
            self, 
            name: str,
            tracker: Tracker,
            input : DataDispatcher,
            output : DataDispatcher,
            recv_timeout_s: int = 10
        ) -> None:

        super().__init__(input,output,recv_timeout_s)

        self.tracker = tracker
        self.overlay = None
        self.name = name

    def post_recv(self, args: Any) -> Any:
        timestamp, index, image = args
        tracking = self.tracker.track(image)
        print(f'{self.name} received image {index}, timestamp {timestamp}',flush=True)
        
        ret = (index,timestamp,tracking)
        return ret
    
class TrackerDisplay(DataProcessingNode):
    def __init__(
            self, 
            track_display: TrackerDisplay, 
            input : DataDispatcher,
            output : DataDispatcher,
            recv_timeout_s: int = 10,
            name: str = 'TrackerDisplay' 
        ) -> None:
        
        super().__init__(input,output,recv_timeout_s)
        self.name = name
        self.track_display = track_display
        self.last_frame = 0
        self.discarded_frames = []

    def pre_loop(self) -> None:
        self.track_display.init_window()

    def post_loop(self) -> None:
        super().post_loop()
        self.track_display.close_window()
        print(f'discarded {len(self.discarded_frames)} frames')

    def post_recv(self, args: Any) -> Any:
        timestamp, index, tracking = args
        if index > self.last_frame:
            self.track_display.display(tracking)
            print(f'{self.name} received image {index}, timestamp {timestamp}',flush=True)
            self.last_frame = index
        else:
            self.discarded_frames.append(index)

class Stimulus(DataProcessingNode):
    def __init__(
            self, 
            stimulus: Stimulus,
            input : DataDispatcher,
            output : DataDispatcher,
            recv_timeout_s: int = 10,
            name: str = 'Stimulus' 
        ) -> None:
        
        super().__init__(input,output,recv_timeout_s)
        
        self.stimulus = stimulus
        self.name = name
        self.last_frame = 0
        self.discarded_frames = []

    def pre_loop(self) -> None:
        self.stimulus.init_window()

    def post_loop(self) -> None:
        super().post_loop()
        self.stimulus.close_window()
        print(f'discarded {len(self.discarded_frames)} frames')

    def post_recv(self, args: Any) -> Any:
        index, timestamp, tracking = args
        if index > self.last_frame:
            print(f'{self.name} received image {index}, timestamp {timestamp}',flush=True)
            self.stimulus.project(tracking)
            self.last_frame = index
        else:
            self.discarded_frames.append(index)
    
class Projector(DataProcessingNode):
    def __init__(
            self, 
            projector : Projector,
            input : DataDispatcher,
            output : DataDispatcher,
            recv_timeout_s: int = 10,
            name: str = 'Projector' 
        ) -> None:
        
        super().__init__(input,output,recv_timeout_s)
        self.projector = projector
        self.name = name
        self.last_frame = 0
        self.discarded_frames = []

    def pre_loop(self) -> None:
        self.projector.init_window()

    def post_loop(self) -> None:
        super().post_loop()
        self.projector.close_window()
        print(f'discarded {len(self.discarded_frames)} frames')

    def post_recv(self, args: Any) -> Any:
        timestamp, index, image = args
        if index > self.last_frame:
            print(f'{self.name} received image {index}, timestamp {timestamp}',flush=True)
            if image is not None:
                self.projector.project(image)
            self.last_frame = index
        else:
            self.discarded_frames.append(index)

class ImageSaver(DataProcessingNode):
    def __init__(
            self, 
            saver : ImageSaver,
            input : DataDispatcher,
            output : DataDispatcher,
            recv_timeout_s: int = 10,
            name: str = 'ImageSaver' 
        ) -> None:
        
        super().__init__(input,output,recv_timeout_s)
        self.saver = saver
        self.name = name

    def post_recv(self, args: Any) -> Any:
        timestamp, index, image = args
        if image is not None:
            print(f'{self.name} received image {index}, timestamp {timestamp}',flush=True)    
            self.saver.write(image)

class DataPlotter(DataProcessingNode):
    def __init__(
            self, 
            plotter : DataPlotter,
            input : DataDispatcher,
            output : DataDispatcher,
            recv_timeout_s: int = 10,
            name: str = 'DataPlotter' 
        ) -> None:
        
        super().__init__(input,output,recv_timeout_s)
        self.plotter = plotter
        self.name = name

    def post_recv(self, args: Any) -> Any:
        self.plotter.format_data(args)