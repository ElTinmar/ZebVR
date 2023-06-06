import numpy
import zmq

def send_array(socket, A, flags=0, copy=True, track=False) -> None:
    """send a numpy array with metadata"""
    md = dict(
        dtype=str(A.dtype),
        shape=A.shape,
    )
    socket.send_json(md, flags | zmq.SNDMORE)
    socket.send(A, flags, copy=copy, track=track)

def recv_array(socket, flags=0, copy=True, track=False):
    """recv a numpy array"""
    md = socket.recv_json(flags=flags)
    msg = socket.recv(flags=flags, copy=copy, track=track)
    buf = memoryview(msg)
    A = numpy.frombuffer(buf, dtype=md["dtype"])
    return A.reshape(md["shape"])

def send_frame(socket, data, flags=0, copy=True, track=False) -> None:
    msg = dict(
        index = data['index'],
        timestamp = data['timestamp']
    )
    socket.send_json(msg, flags | zmq.SNDMORE)
    send_array(socket, data['frame'], flags, copy, track)

def recv_frame(socket, flags=0, copy=True, track=False):
    msg = socket.recv_json(flags=flags)
    ret = {
        'index': msg["index"],
        'timestamp': msg["timestamp"],
        'frame': recv_array(socket, flags, copy, track)
    }
    return ret