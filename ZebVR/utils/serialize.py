from typing import Callable, Any, Dict
from collections import deque

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