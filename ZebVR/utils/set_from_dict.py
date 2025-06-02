from typing import Callable, Any, Dict, TypeVar
import logging

K = TypeVar('K')   # Key type for the dictionary
V = TypeVar('V')   # Value type expected by setter (and returned by cast)

def set_from_dict(
        dictionary: Dict[K, Any],
        key: K,
        setter: Callable[[V], None],
        default: Any,
        cast: Callable[[Any], V] = lambda x: x  # no-op cast by default
    ) -> None:
    """
    Retrieve a value from `dictionary` by `key`, cast it to the desired type,
    and apply it using `setter`. If the key is missing or casting fails,
    `default` is used instead.

    Parameters:
        dictionary (Dict[K, Any]): Source dictionary.
        key (K): Key to look up.
        setter (Callable[[V], None]): Function to apply the value.
        default (V): Fallback value.
        cast (Callable[[Any], V]): Cast function (default: identity).

    Exceptions:
        Catches ValueError and TypeError raised by `cast`.
    """
    
    try:
        value = dictionary.get(key, default)
        setter(cast(value))
        
    except (ValueError, TypeError) as e:
        logging.warning(
            f"set_from_dict: failed to set value for key '{key}'.\n"
            f"default used: {default}.\n" 
            f"Error: {e}"
        )        
        setter(cast(default))