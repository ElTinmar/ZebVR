import numpy as np
import matplotlib.pyplot as plt
from typing import Callable, Tuple
from PIL import Image

radial_profile = Callable[[np.ndarray], np.ndarray]

def linear_profile(r_norm: np.ndarray) -> np.ndarray:
    return 1 - r_norm  

cos_exp = 10
def cosine_profile(r_norm: np.ndarray) -> np.ndarray:
    return np.cos(np.pi/2*r_norm)**cos_exp  


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


def save_svg(x, y, radius_mm: float, filename="polka_dots.svg", dot_diameter_mm=0.2, color='blue'):
    """Save dot coordinates as SVG vector circles."""
    size = 2 * radius_mm

    with open(filename, "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}mm" height="{size}mm" viewBox="{-radius_mm} {-radius_mm} {size} {size}">\n')
        for xi, yi in zip(x, y):
            f.write(f'<circle cx="{xi:.3f}" cy="{-yi:.3f}" r="{dot_diameter_mm/2:.3f}" fill={color} />\n')
        f.write('</svg>\n')
    print(f"Saved {len(x)} dots to {filename}")

if __name__ == '__main__':

    r = 25.4
    x,y = generate_dots(r, cosine_profile, num_dots_max= 5_000_000)
    resolution_pix_per_mm = 50

    arr = 255*np.ones((int(resolution_pix_per_mm*2*r), int(resolution_pix_per_mm*2*r)), dtype=np.uint8)
    row, col = y*resolution_pix_per_mm + r*resolution_pix_per_mm, x*resolution_pix_per_mm + r*resolution_pix_per_mm
    arr[row.astype(np.uint), col.astype(np.uint)] = 0
    img = Image.fromarray(arr)
    dpi = resolution_pix_per_mm*25.4
    img.save("polka_dots_cos10_5M.png", dpi=(dpi, dpi))
    plt.imshow(arr, cmap='gray')
    plt.show(block=False)
    

    save_svg(x,y,r,filename="polka_dots.svg", dot_diameter_mm=0.2)

    # Plot profile
    plt.figure(figsize=(6,6))
    r_norm = np.linspace(0,1,100)
    plt.plot(r_norm, polynomial_profile(r_norm))
    plt.show(block=False)

    # Plot profile
    plt.figure(figsize=(6,6))
    r_norm = np.linspace(0,1,100)
    plt.plot(r_norm, cosine_profile(r_norm))
    plt.show(block=False)

    # Plot dots
    plt.figure(figsize=(6,6))
    plt.scatter(x, y, s=1, color='blue')
    plt.axis('equal')
    plt.axis('off')
    plt.show()
