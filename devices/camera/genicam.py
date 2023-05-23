from harvesters.core import Harvester
import json
from devices.camera.camera import Camera, BufferAdapter

class BufferHarvesters(BufferAdapter):
    def __init__(self, buffer):
        self._buffer = buffer

    def get_img(self):
        return self._buffer.payload.component[0].data
    
    def get_timestamp(self):
        return self._buffer.timestamp

    def queue(self):
        """This is important to allow the camera to reuse the buffer"""
        self._buffer.queue()

class GenicamHarvesters(Camera):
    def __init__(self, ini_file, gentl_producer):
        """
        Open camera using the GenICam/GenTL API
        Inputs:
            gentl_producer: *.cti file from camera vendor     
        """

        super().__init__(ini_file)
        self._h = Harvester()
        self._h.add_file(gentl_producer)
        self._h.update()

        # discover cameras
        if ~self._h.device_info_list:
            RuntimeError('No camera found')
        else:
            print(f"Found {len(self._h.device_info_list)} devices")

        # open and configure camera
        print("Selecting camera:")
        print(json.dumps(self._h.device_info_list[self._camera_index]))

        # TODO
        # dir(ia.remote_device.node_map) returns available GenICam feature nodes
        # use this to check that the properties you are trying to set exist
        # check also the GenICam SFNC for standard names

        self._imAcq = self._h.create(self._camera_index)
        self._imAcq.num_buffers = self._num_buffers
        node_map = self._imAcq.remote_device.node_map

        def configure_node(self,node,value):
            # check node mode: available, not implemented, not available, ...
            # check node type: int, bool, enum, ...
            # check allowed range for the node, or enum states
            # set the value
            # get the value to check if it worked
            pass

        node_map.Width.value = self._width
        node_map.Height.value = self._height
        node_map.OffsetX.value = self._left
        node_map.OffsetY.value = self._top
        node_map.PixelFormat.value = self._pixel_format
        node_map.AcquisitionFrameRate.value = self._fps
        node_map.TriggerMode.value = self._triggers
        node_map.Gain.value = self._gain
        node_map.ExposureTime.value = self._exposure_time

        # TODO print settings

    def start_acquisition(self):
        self._imAcq.start()

    def stop_acquisition(self):
        self._imAcq.stop()

    def fetch(self):
        # TODO check that it is passed by reference and there is no copy
        # and that the buffer is not destroyed at the end of the function
        buf = BufferHarvesters(self._imAcq.fetch())
        return buf
    
    def __del__(self):
        print(self._imAcq.statistics)
        self._imAcq.destroy()
        self._h.reset()