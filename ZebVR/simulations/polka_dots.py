import numpy as np
import matplotlib.pyplot as plt
from typing import Callable, Tuple

radial_profile = Callable[[np.ndarray], np.ndarray]

def linear_profile(r_norm: np.ndarray) -> np.ndarray:
    return 1 - r_norm  

# Polynomial radial profile coefficients (T(r) = a0 + a1*r + a2*r^2 + ...)
coeffs = [1.0, 0.0, -1.0]  # example: T(r) = 1 - r^2

def polynomial_profile(r_norm: np.ndarray) -> np.ndarray:
    T = sum(a * r_norm**i for i, a in enumerate(coeffs))
    return np.clip(T, 0, 1)
    
def generate_dots(
        radius: float, 
        profile: radial_profile, 
        num_dots_max: int = 10000
    ) -> Tuple[np.ndarray, np.ndarray]:

    # Generate candidate points uniformly
    x = np.random.uniform(-radius, radius, num_dots_max)
    y = np.random.uniform(-radius, radius, num_dots_max)
    r = np.sqrt(x**2 + y**2)
    inside = r <= radius
    x, y, r = x[inside], y[inside], r[inside]

    # Decide which points become dots based on density profile
    r_norm = r / radius                  # normalize radius 0->1
    prob = profile(r_norm)  # probability of dot
    mask = np.random.rand(len(r)) < prob

    return x[mask], y[mask]

if __name__ == '__main__':

    r = 200
    x,y = generate_dots(r, polynomial_profile)
    
    # Plot profile
    plt.figure(figsize=(6,6))
    r_norm = np.linspace(0,1,100)
    plt.plot(r_norm, polynomial_profile(r_norm))
    plt.show(block=False)

    # Plot dots
    plt.figure(figsize=(6,6))
    plt.scatter(x, y, s=1, color='black')
    plt.axis('equal')
    plt.axis('off')
    plt.show()
