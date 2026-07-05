from typing import Callable, Any, Dict, Optional
from collections import deque
import cv2
import base64
import numpy as np

def get_attributes(obj: Any) -> Dict[str, Any]:
    result = {}

    # Start with class attributes (exclude callables and special names)
    cls = obj.__class__
    for k, v in cls.__dict__.items():
        if not k.startswith("_") and not callable(v):
            result[k] = v

    # Overlay instance attributes
    if hasattr(obj, "__dict__"):
        result.update(obj.__dict__)

    return result

def serialize(obj: Any, serializers: Dict[Any, Callable]):

    for t, func in serializers.items():
        if isinstance(obj, t):
            return func(obj)
        
    if isinstance(obj, dict):
        return {k: serialize(v, serializers) for k, v in obj.items()}
    
    if isinstance(obj, (list, tuple, deque)):
        return [serialize(v, serializers) for v in obj]

    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
        
    attrs = get_attributes(obj)
    if attrs:
        return serialize(attrs, serializers)

    return repr(obj)


def ndarray_to_b64_png(image: np.ndarray) -> str:
    """
    Compresses a NumPy image array into a PNG and encodes it to a Base64 string 
    suitable for JSON serialization. Returns an empty string if compression fails.
    """
    if image is None or image.size == 0:
        return ""
    
    success, encoded_img = cv2.imencode('.png', image)
    if not success:
        return ""
        
    return base64.b64encode(encoded_img).decode('utf-8')


def b64_png_to_ndarray(b64_string: str) -> Optional[np.ndarray]:
    """
    Decodes a Base64 PNG string back into a standard NumPy image array.
    Returns None if the string is empty or invalid.
    """
    if not b64_string:
        return None
        
    try:
        img_bytes = base64.b64decode(b64_string)
        nparr = np.frombuffer(img_bytes, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception:
        # Catch decoding or corruption errors gracefully
        return None