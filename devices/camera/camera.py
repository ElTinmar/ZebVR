from configparser import ConfigParser
from abc import ABC, abstractmethod
import logging

class BufferAdapter(ABC):
    """
    Adapter class to provide camera image and timestamps
    with a unified interface accross vendors.
    Also provides the queue method to reallocate images
    to the camera buffer 
    """

    @abstractmethod
    def get_img(self):
        """return image data"""
    
    @abstractmethod
    def get_timestamp(self):
        """return timestamps in ns"""

    @abstractmethod
    def queue(self):
        """return buffer to camera"""

class Camera(ABC):
    """
    Specify a unified interface to interact with cameras from
    different vendors / with different physical connection to 
    the computer
    """

    def __init__(self, ini_file):
        """
        Read camera parameters relevant to an experiment from 
        an INI file with a simple structure 
        """
        # read ini file
        config = ConfigParser()
        config.read(ini_file)
        
        self._camera_index = int(config['camera'].get('camera_index', '0'))
        self._exposure_time = int(config['camera'].get('exposure_time', '1000'))
        self._gain = int(config['camera'].get('gain', '1'))
        self._top = int(config['camera'].get('top', '0'))
        self._left = int(config['camera'].get('left', '0'))
        self._height = int(config['camera'].get('height', '1024'))
        self._width = int(config['camera'].get('width', '1024'))
        self._triggers = config['camera'].get('triggers', 'Off')
        self._fps = int(config['camera'].get('fps', '200'))
        self._pixel_format = config['camera'].get('pixel_format', 'Mono8')
        self._num_frames = int(config['camera'].get('num_frames', '100'))
        self._num_buffers = int(config['camera'].get('num_buffers', '100'))

        self._logger = logging.getLogger('Camera')

    @abstractmethod
    def start_acquisition(self):
        """Start image acquisition"""

    @abstractmethod
    def stop_acquisition(self):
        """Stop camera acquisition"""

    @abstractmethod
    def fetch(self):
        """Fetch buffer from the camera"""

    def get_height(self):
        return self._height

    def get_width(self):
        return self._width

    def get_num_frames(self):
        return self._num_frames
    
    def get_fps(self):
        return self._fps
    
