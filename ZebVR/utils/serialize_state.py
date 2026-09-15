"""
state_io.py — shared serializer for .vr / .metadata files.

Walks a nested dict/list structure, converts everything to plain JSON-safe
types, and extracts array-like objects (numpy arrays, array.array, pandas
Series/DataFrames, and anything else you register) into standalone files
inside a sibling `<name>_arrays/` folder. Leaves a human-readable JSON tree
with pointers to those files.

To support a new array-like type without modifying this module, call
`register_array_handler()` from wherever that type is defined/used.
"""
import json
import re
from array import array as array_type
from collections import deque
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

import numpy as np


# ---------------------------------------------------------------------------
# Pluggable array-type handlers
# ---------------------------------------------------------------------------

@dataclass
class ArrayHandler:
    type_name: str                              # tag stored in JSON, must be unique
    matches: Callable[[Any], bool]               # isinstance/predicate check
    save: Callable[[Any, Path], str]             # (obj, path_no_suffix) -> filename written
    load: Callable[[Path], Any]                  # (full_path) -> reconstructed obj
    to_inline: Callable[[Any], Any]              # fallback used when extract_arrays=False


ARRAY_HANDLERS: List[ArrayHandler] = []
_HANDLERS_BY_NAME: Dict[str, ArrayHandler] = {}


def register_array_handler(handler: ArrayHandler) -> None:
    """Register a new array-like type for separate-file extraction.

    Handlers are checked in registration order; the first match wins.
    Call this anywhere (including outside this module) to add support
    for new types without editing state_io.py.
    """
    ARRAY_HANDLERS.append(handler)
    _HANDLERS_BY_NAME[handler.type_name] = handler


def _find_handler(obj: Any) -> Optional[ArrayHandler]:
    for handler in ARRAY_HANDLERS:
        if handler.matches(obj):
            return handler
    return None


# --- built-in handler: numpy.ndarray -----------------------------------------

def _save_ndarray(arr: np.ndarray, path: Path) -> str:
    np.save(path.with_suffix(".npy"), arr)
    return f"{path.name}.npy"

register_array_handler(ArrayHandler(
    type_name="ndarray",
    matches=lambda o: isinstance(o, np.ndarray),
    save=_save_ndarray,
    load=lambda p: np.load(p),
    to_inline=lambda o: o.tolist(),
))


# --- built-in handler: array.array --------------------------------------------
# array.array needs its `typecode` to be reconstructed correctly, which isn't
# recoverable from a .npy file alone. That extra bit of metadata is stashed
# directly in the JSON pointer (see _save_typed / load_state below), so this
# handler's `load` is a placeholder — the real loading logic lives in
# `_load_stdlib_array`, dispatched specially by type_name in load_state().

def _save_stdlib_array(arr: array_type, path: Path) -> str:
    np.save(path.with_suffix(".npy"), np.asarray(arr))
    return f"{path.name}.npy"

def _load_stdlib_array(path: Path, typecode: str) -> array_type:
    return array_type(typecode, np.load(path).tolist())

register_array_handler(ArrayHandler(
    type_name="array",
    matches=lambda o: isinstance(o, array_type),
    save=_save_stdlib_array,
    load=lambda p: p,  # unused directly; see _load_stdlib_array
    to_inline=lambda o: o.tolist(),
))



# ---------------------------------------------------------------------------
# Core recursive walk
# ---------------------------------------------------------------------------

def _sanitize(key_path: str) -> str:
    name = re.sub(r'[^\w\-]', '_', key_path)
    return name[len("root_"):] if name.startswith("root_") else name


def _to_safe(obj: Any, key_path: str, exclude_keys: Set[str],
             array_dir: Optional[Path], used_names: set) -> Any:

    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            child_path = f"{key_path}.{k}" if key_path else k
            if child_path in exclude_keys or k in exclude_keys:
                continue
            if callable(v):
                continue
            out[k] = _to_safe(v, child_path, exclude_keys, array_dir, used_names)
        return out

    if isinstance(obj, (list, tuple, deque)):
        return [_to_safe(v, f"{key_path}_{i}", exclude_keys, array_dir, used_names)
                for i, v in enumerate(obj)]

    handler = _find_handler(obj)
    if handler is not None:
        if array_dir is None:
            return handler.to_inline(obj)
        return _save_typed(obj, handler, key_path, array_dir, used_names)

    if isinstance(obj, Path):
        return obj.as_posix()

    if isinstance(obj, Enum):
        return obj.value

    if isinstance(obj, np.generic):
        return obj.item()

    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj

    raise TypeError(
        f"Unrecognized type '{type(obj).__name__}' at '{key_path}'. "
        f"Value: {obj!r}. Register an ArrayHandler, add inline handling "
        f"in _to_safe(), or add its key to exclude_keys."
    )


def _save_typed(obj: Any, handler: ArrayHandler, key_path: str,
                array_dir: Path, used_names: set) -> dict:
    base_name = _sanitize(key_path)
    name, counter = base_name, 1
    while name in used_names:
        name = f"{base_name}_{counter}"
        counter += 1
    used_names.add(name)

    array_dir.mkdir(parents=True, exist_ok=True)
    filename = handler.save(obj, array_dir / name)

    pointer = {"__serialized_type__": handler.type_name, "file": filename}
    if isinstance(obj, array_type):
        pointer["typecode"] = obj.typecode  # extra metadata needed for reconstruction
    return pointer


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def save_state(state: dict, json_path: Path, exclude_keys: Optional[Set[str]] = None,
               extract_arrays: bool = True, indent: int = 2) -> None:
    """
    Serialize a nested dict to JSON, extracting array-like values into a
    sibling `<name>_arrays/` folder.

    :param state: The nested dictionary to save.
    :param json_path: Destination path for the JSON file (e.g. "run.vr").
    :param exclude_keys: Dotted-path or bare keys to skip entirely
        (e.g. "camera.camera_constructor", or just "daq").
    :param extract_arrays: If True (default), array-like values are saved to
        separate files and referenced by pointer. If False, they're inlined
        as plain JSON (lists) — only recommended for small arrays.
    :param indent: JSON indentation level.
    """
    json_path = Path(json_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)

    array_dir = json_path.parent / f"{json_path.stem}_arrays" if extract_arrays else None
    safe_state = _to_safe(state, "", exclude_keys or set(), array_dir, used_names=set())

    payload = {"__array_dir__": array_dir.name, "data": safe_state} if array_dir else safe_state
    json_path.write_text(json.dumps(payload, indent=indent), encoding="utf-8")


class MissingArrayError(FileNotFoundError):
    """Raised when one or more referenced array files can't be found on load."""
    def __init__(self, missing_paths: List[str]):
        self.missing_paths = missing_paths
        super().__init__(f"{len(missing_paths)} missing array file(s): {missing_paths}")


def load_state(json_path: Path, strict: bool = True) -> dict:
    """
    Deserialize a JSON file previously written by `save_state`, reconstructing
    any extracted arrays from disk.

    :param json_path: Path to the JSON file.
    :param strict: If True (default), raise `MissingArrayError` if any
        referenced array file is missing. If False, missing arrays are
        replaced with `None` and loading proceeds for everything else.
    :return: Reconstructed dictionary.
    """
    json_path = Path(json_path)
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    if isinstance(payload, dict) and "__array_dir__" in payload:
        array_dir = json_path.parent / payload["__array_dir__"]
        data = payload["data"]
    else:
        # Old-format file (no array extraction) or extract_arrays=False was used.
        array_dir, data = None, payload

    missing: List[str] = []

    def hook(item):
        if isinstance(item, dict):
            type_name = item.get("__serialized_type__")
            if type_name is not None:
                path = array_dir / item["file"]
                if not path.exists():
                    missing.append(str(path))
                    return None
                if type_name == "array":
                    return _load_stdlib_array(path, item["typecode"])
                return _HANDLERS_BY_NAME[type_name].load(path)
            return {k: hook(v) for k, v in item.items()}
        if isinstance(item, list):
            return [hook(v) for v in item]
        return item

    result = hook(data)

    if missing and strict:
        raise MissingArrayError(missing)

    return result