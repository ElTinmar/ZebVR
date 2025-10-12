from typing import Callable, Any, Dict
from collections import deque

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
        
    if hasattr(obj, "__dict__"):
        if obj.__dict__:
            return serialize(obj.__dict__, serializers)

    return repr(obj)