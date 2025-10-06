import numpy as np
import matplotlib.pyplot as plt
from typing import Callable
from tqdm import tqdm


# --------------------------------------- top: ground-glass diffusion layer
#                 Glass
# --------------------------------------- interface water glass
#
#
#                 Water
#
#
# --------------------------------------- bottom


def square_boundaries(x: np.ndarray, y: np.ndarray, b: float) -> np.ndarray:
    return (x>=-b) & (x<=b) & (y>=-b) & (y<=b)

def disk_boundaries(x: np.ndarray, y: np.ndarray, r: float) -> np.ndarray:
    return x**2 + y**2 <= r**2

def bilinear_interpolate(grid: np.ndarray, x: np.ndarray, y: np.ndarray, grid_size: float) -> np.ndarray:

    N = grid.shape[0]
    # map x, y from [-grid_size/2, grid_size/2] to [0, N-1]
    xi = (x + grid_size/2) * (N-1) / grid_size
    yi = (y + grid_size/2) * (N-1) / grid_size

    # integer part
    x0 = np.floor(xi).astype(int)
    y0 = np.floor(yi).astype(int)
    # fractional part
    dx = xi - x0
    dy = yi - y0

    # clamp indices to grid bounds
    x0 = np.clip(x0, 0, N-2)
    y0 = np.clip(y0, 0, N-2)
    x1 = x0 + 1
    y1 = y0 + 1

    # corners
    Q11 = grid[y0, x0]
    Q21 = grid[y0, x1]
    Q12 = grid[y1, x0]
    Q22 = grid[y1, x1]

    # bilinear interpolation formula
    interpolated = (Q11 * (1-dx) * (1-dy) +
                    Q21 * dx * (1-dy) +
                    Q12 * (1-dx) * dy +
                    Q22 * dx * dy)
    return interpolated

def map_image(
        x_bottom: float, y_bottom: float, 
        X_interface: np.ndarray, Y_interface: np.ndarray, 
        top_intensity: np.ndarray,
        n_water: float, n_glass: float,
        water_depth: float, glass_thickness: float, 
        water_absorption_coefficient: float, glass_absorption_coefficient: float, 
        glass_size_mm: float, boundaries: Callable[[np.ndarray, np.ndarray, float], np.ndarray],
        absorption: bool
    ) -> np.ndarray:

    # trace rays in the water
    dx_water, dy_water = X_interface - x_bottom, Y_interface - y_bottom
    r_water = np.sqrt(dx_water**2 + dy_water**2 + water_depth**2) # ray length in water
    theta_w = np.arccos(water_depth / r_water) # ray angle at the water-glass interface
    phi_w = np.arctan2(dy_water, dx_water) # ray angle in the XY plane

    # trace rays in the glass
    theta_g = np.arcsin(n_water/n_glass * np.sin(theta_w)) # Snell's law
    r_glass = glass_thickness / np.cos(theta_g) # ray length in glass   
    l_top = glass_thickness * np.tan(theta_g)
    dx_glass, dy_glass = l_top * np.cos(phi_w), l_top * np.sin(phi_w)
    x_top, y_top = X_interface + dx_glass, Y_interface + dy_glass

    I = bilinear_interpolate(top_intensity, x_top, y_top, glass_size_mm)
    
    # compute intensity
    intensity: np.ndarray = I * np.cos(theta_g) 
    if absorption:
        intensity *= np.exp(-water_absorption_coefficient * r_water)
        intensity *= np.exp(-glass_absorption_coefficient * r_glass)

    # check boudaries
    valid = boundaries(x_top, y_top, glass_size_mm/2) 
    intensity[~valid] = 0
    
    return intensity

def run_sim(
    glass_size_mm: float = 50.0,
    bottom_size_mm: float = 100.0,
    num_points_interface: int = 101,
    num_points_bottom: int = 101,
    glass_thickness: float = 1.6,
    water_depth: float = 5.0,
    n_glass: float = 1.45,
    n_water: float = 1.33,
    water_absorption_coefficient: float = 0.001,   
    glass_absorption_coefficient: float = 0.00000001,
    boundaries: Callable[[np.ndarray, np.ndarray, float], np.ndarray] = square_boundaries,
    absorption: bool = False
) -> np.ndarray:
    
    # Water-glass interface
    points_interface = np.linspace(-glass_size_mm/2, glass_size_mm/2, num_points_interface)
    X_interface, Y_interface = np.meshgrid(points_interface, points_interface)

    # Bottom of the dish
    points_bottom = np.linspace(-bottom_size_mm/2, bottom_size_mm/2, num_points_bottom)
    X_bottom, Y_bottom = np.meshgrid(points_bottom, points_bottom)
        
    intensity = np.zeros_like(X_bottom)
    for i in tqdm(range(num_points_bottom)):
        for j in range(num_points_bottom):
            intensity[i,j] = np.nansum(
                map_image(
                    X_bottom[i,j], Y_bottom[i,j], 
                    X_interface, Y_interface, 
                    np.ones(1),
                    n_water, n_glass,
                    water_depth, glass_thickness, 
                    water_absorption_coefficient, glass_absorption_coefficient, 
                    glass_size_mm, boundaries,
                    absorption
                )
            )

    return intensity

def plot_sim(
    intensity: np.ndarray,
    num_points_bottom: int = 101,
    bottom_size_mm: float = 100.0,
) -> None:

    # Plot
    points_bottom = np.linspace(-bottom_size_mm/2, bottom_size_mm/2, num_points_bottom)
    row_idx = num_points_bottom // 2
    y_coord = points_bottom[row_idx]

    fig, ax = plt.subplots(1, 2, figsize=(12, 6))
    im = ax[0].imshow(
        intensity, 
        extent = [-bottom_size_mm/2, bottom_size_mm/2, -bottom_size_mm/2, bottom_size_mm/2],
        origin = 'lower', 
        cmap = 'inferno'
    )
    fig.colorbar(im, ax=ax[0], label='Normalized intensity')
    ax[0].set_title('Intensity profile')
    ax[0].set_xlabel('x (mm)')
    ax[0].set_ylabel('y (mm)')
    ax[0].axhline(y=y_coord, color='cyan', linestyle='--', linewidth=1.5)

    ax[1].plot(points_bottom, intensity[row_idx, :], color='cyan')
    ax[1].set_xlabel('x (mm)')
    ax[1].set_ylabel('Normalized Intensity')

    plt.tight_layout()
    plt.show(block=False)

def plot_image(    
    intensity: np.ndarray,
    glass_size_mm: float
):
    
    fig = plt.figure(figsize=(6, 6))
    im = plt.imshow(
        intensity, 
        extent = [-glass_size_mm/2, glass_size_mm/2, -glass_size_mm/2, glass_size_mm/2],
        origin = 'lower', 
        cmap = 'inferno'
    )
    plt.title('Intensity profile')
    plt.xlabel('x (mm)')
    plt.ylabel('y (mm)')
    plt.show(block=False)
        
def checkerboard(N: int, square_size: int) -> np.ndarray:
    n_squares = N // square_size
    basic = np.indices((n_squares, n_squares)).sum(axis=0) % 2
    checkerboard = np.kron(basic, np.ones((square_size, square_size)))
    return checkerboard[:N, :N]

if __name__ == '__main__':
    
    ## IR illumination
    num_points_bottom = 101 
    num_points_interface = 401

    # glass-water
    intensity = run_sim(
        absorption = False,
        num_points_bottom = num_points_bottom, 
        num_points_interface = num_points_interface
    )
    plot_sim(
        intensity,
        num_points_bottom = num_points_bottom
    )

    # air-water
    intensity = run_sim(
        absorption = False,
        num_points_bottom = num_points_bottom, 
        num_points_interface = num_points_interface,
        n_glass = 1.0 # air
    )
    plot_sim(
        intensity,
        num_points_bottom = num_points_bottom
    )

    ## image from a single point
    x_b, y_b = 0, 0

    points_interface = np.linspace(-50/2, 50/2, num_points_interface)
    X_interface, Y_interface = np.meshgrid(points_interface, points_interface)
    intensity = map_image(
        x_bottom=x_b, y_bottom=y_b, 
        X_interface=X_interface, Y_interface=Y_interface, 
        top_intensity=checkerboard(256,16),
        n_water=1.33, n_glass=1.45,
        water_depth=5, glass_thickness=1.6, 
        water_absorption_coefficient=0.001, glass_absorption_coefficient=1e-8, 
        glass_size_mm=50, boundaries=square_boundaries,
        absorption=False
    )
    plot_image(
        intensity,
        glass_size_mm=50
    )

    points_interface = np.linspace(-50/2, 50/2, num_points_interface)
    X_interface, Y_interface = np.meshgrid(points_interface, points_interface)
    intensity = map_image(
        x_bottom=x_b, y_bottom=y_b, 
        X_interface=X_interface, Y_interface=Y_interface, 
        top_intensity=checkerboard(256,16),
        n_water=1.33, n_glass=1.0,
        water_depth=5, glass_thickness=1.6, 
        water_absorption_coefficient=0.001, glass_absorption_coefficient=1e-8, 
        glass_size_mm=50, boundaries=square_boundaries,
        absorption=False
    )
    plot_image(
        intensity,
        glass_size_mm=50
    )
