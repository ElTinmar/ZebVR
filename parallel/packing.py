import sys

def pack_frame(
        buffer,
        sentinel,
        frame_num,
        timestamp,
        height,
        width,
        channels,
        pixel_data
    ) -> None:

    buffer[:1] = memoryview(sentinel.to_bytes(1,sys.byteorder))
    buffer[1:5] = memoryview(frame_num.to_bytes(4,sys.byteorder))
    buffer[5:13] = memoryview(timestamp.to_bytes(8,sys.byteorder))
    buffer[13:17] = memoryview(height.to_bytes(4,sys.byteorder))
    buffer[17:21] = memoryview(width.to_bytes(4,sys.byteorder))
    buffer[21:22] = memoryview(channels.to_bytes(1,sys.byteorder))
    buffer[22:] = pixel_data

def unpack_frame(buffer):

    sentinel = int.from_bytes(buffer[:1], sys.byteorder)
    frame_num = int.from_bytes(buffer[1:5], sys.byteorder)
    timestamp = int.from_bytes(buffer[5:13], sys.byteorder)
    height = int.from_bytes(buffer[13:17], sys.byteorder)
    width = int.from_bytes(buffer[17:21], sys.byteorder)
    channels = int.from_bytes(buffer[21:22], sys.byteorder)
    pixel_data = buffer[22:]
    return (sentinel, frame_num, timestamp, height, width, channels, pixel_data)

def pack_tracking():
    pass

def unpack_tracking():
    pass
