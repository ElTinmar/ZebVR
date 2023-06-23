import numpy as np
from scipy import ndimage as ndi
import time
from numpy.typing import NDArray
from typing import Tuple
# those are essentially stripped down versions of 
# skimage.morphology.remove_small_objects

def components_size(
        ar: NDArray, 
        connectivity: int = 1
    ) -> Tuple[NDArray, NDArray]:
    
    footprint = ndi.generate_binary_structure(ar.ndim, connectivity)
    label = np.zeros_like(ar, dtype=np.int32)
    ndi.label(ar, footprint, output=label)
    component_sz = np.bincount(label.ravel()) 
    return (component_sz, label)

def bwareaopen(
        ar: NDArray, 
        min_size: int = 64, 
        connectivity: int = 1
        ) -> Tuple[NDArray, NDArray]:

    out = ar.copy()
    component_sz, label = components_size(ar, connectivity)
    too_small = component_sz < min_size
    too_small_mask = too_small[label]
    out[too_small_mask] = 0
    label[label == too_small] = 0
    return (out, label)

def bwareafilter(
        ar: NDArray, 
        min_size: int = 64, 
        max_size: int = 256, 
        connectivity: int = 1
        ) -> Tuple[NDArray,NDArray]:
    
    out = ar.copy()
    component_sz, label = components_size(ar, connectivity)
    too_small = component_sz < min_size 
    too_small_mask = too_small[label]
    too_big = component_sz > max_size
    too_big_mask = too_big[label]
    out[too_small_mask] = 0
    out[too_big_mask] = 0
    label[label == too_small] = 0
    label[label == too_big] = 0
    return (out, label)