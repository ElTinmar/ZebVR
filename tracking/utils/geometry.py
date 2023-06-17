import numpy as np
from numpy.typing import NDArray

def ellipse_direction(inertia_tensor: NDArray) -> NDArray:
    '''
    Get ellipse orientation: return the first eigenvector 
    of the inertia tensor, which corresponds to the principal 
    axis of the ellipse 
    '''
    eigvals, eigvecs = np.linalg.eig(inertia_tensor)
    loc = np.argmax(abs(eigvals))
    return eigvecs[loc,:]

def angle_between_vectors(v1: NDArray, v2: NDArray) -> float:
    v1_unit = v1 / np.linalg.norm(v1)
    v2_unit = v2 / np.linalg.norm(v2)
    return np.array(np.arccos(np.dot(v1_unit,v2_unit)))

