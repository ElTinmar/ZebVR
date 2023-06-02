import numpy as np
from scipy import ndimage as ndi
import time

# those are essentially stripped down versions of 
# skimage.morphology.remove_small_objects

def components_size(ar, connectivity=1):
    #start_time_ns = time.process_time_ns()
    footprint = ndi.generate_binary_structure(ar.ndim, connectivity)
    #print(f'generate_binary_structure {10e-9 *(time.process_time_ns() - start_time_ns)}')
    ccs = np.zeros_like(ar, dtype=np.int32)
    ndi.label(ar, footprint, output=ccs)
    #print(f'label {10e-9 *(time.process_time_ns() - start_time_ns)}')
    component_sz = np.bincount(ccs.ravel())
    #print(f'bincount {10e-9 *(time.process_time_ns() - start_time_ns)}')
    
    return (component_sz, ccs)

def bwareaopen(ar, min_size=64, connectivity=1):
    
    out = ar.copy()
    component_sz, ccs = components_size(ar, connectivity)
    too_small = component_sz < min_size
    too_small_mask = too_small[ccs]
    out[too_small_mask] = 0

    return out

def bwareafilter(ar, min_size=64, max_size=256, connectivity=1):
    
    out = ar.copy()
    component_sz, ccs = components_size(ar, connectivity)
    too_small = component_sz < min_size 
    too_small_mask = too_small[ccs]
    too_big = component_sz > max_size
    too_big_mask = too_big[ccs]
    out[too_small_mask] = 0
    out[too_big_mask] = 0

    return out