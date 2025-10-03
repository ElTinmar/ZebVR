import numpy as np
import matplotlib.pyplot as plt
from typing import Callable

def square_boundaries(x: np.ndarray, y: np.ndarray, b: float) -> np.ndarray:
    return (x>=-b) & (x<=b) & (y>=-b) & (y<=b)

def disk_boundaries(x: np.ndarray, y: np.ndarray, r: float) -> np.ndarray:
    return x**2 + y**2 <= r**2

def trace_rays(
        x_bottom: float, y_bottom: float, 
        X_interface: np.ndarray, Y_interface: np.ndarray, 
        n_water: float, n_glass: float,
        water_depth: float, glass_thickness: float, 
        water_absorption_coefficient: float, glass_absorption_coefficient: float, 
        glass_size_mm: float, boundaries: Callable[[np.ndarray, np.ndarray, float], np.ndarray],
        square_law: bool, beer_lambert: bool
    ):

    # trace rays in the water
    dx_water, dy_water = X_interface - x_bottom, Y_interface - y_bottom
    r_water = np.sqrt(dx_water**2 + dy_water**2 + water_depth**2)
    theta_w = np.arccos(water_depth / r_water)
    phi_w = np.arctan2(dy_water, dx_water)

    # trace rays in the glass
    theta_g = np.arcsin(n_water/n_glass * np.sin(theta_w))
    r_glass = glass_thickness/np.cos(theta_g)    
    l_top = glass_thickness*np.tan(theta_g)
    dx_glass = l_top * np.cos(phi_w)
    dy_glass = l_top * np.sin(phi_w)
    x_glass = X_interface + dx_glass
    y_glass = Y_interface + dy_glass

    # check boudaries
    valid = boundaries(x_glass, y_glass, glass_size_mm/2) & boundaries(X_interface, Y_interface, glass_size_mm/2)
    
    intensity = np.cos(theta_g) 
    if square_law: # I should probably not do that
        intensity /= (r_water+r_glass)**2 
    if beer_lambert:
        intensity *= np.exp(-water_absorption_coefficient * r_water) * np.exp(-glass_absorption_coefficient * r_glass) 

    intensity[~valid] = 0
    
    return intensity

def run_sim(
    glass_size_mm = 50,
    bottom_size_mm = 100,
    num_points_interface = 101,
    num_points_bottom = 101,
    glass_thickness = 1.6,
    water_depth = 5,
    n_glass = 1.45,
    n_water = 1.33,
    water_absorption_coefficient = 0.001,
    glass_absorption_coefficient = 0.00000001,
    boundaries = square_boundaries,
    square_law = True,
    beer_lambert = True
):
    
    # Water-glass interface
    points_interface = np.linspace(-glass_size_mm/2, glass_size_mm/2, num_points_interface)
    X_interface, Y_interface = np.meshgrid(points_interface, points_interface)

    # Bottom of the dish
    points_bottom = np.linspace(-bottom_size_mm/2, bottom_size_mm/2, num_points_bottom)
    X_bottom, Y_bottom = np.meshgrid(points_bottom, points_bottom)
        
    intensity = np.zeros_like(X_bottom)
    for i in range(num_points_bottom):
        for j in range(num_points_bottom):
            rays = trace_rays(
                X_bottom[i,j], Y_bottom[i,j], 
                X_interface, Y_interface, 
                n_water, n_glass,
                water_depth, glass_thickness, 
                water_absorption_coefficient, glass_absorption_coefficient, 
                glass_size_mm, boundaries,
                square_law, beer_lambert
            )
            intensity[i,j] = np.nansum(rays)

    return intensity

def plot_results(
    intensity,
    num_points_bottom = 101,
    bottom_size_mm = 100,
):

    # Plot
    points_bottom = np.linspace(-bottom_size_mm/2, bottom_size_mm/2, num_points_bottom)
    row_idx = num_points_bottom // 2
    y_coord = points_bottom[row_idx]

    fig, ax = plt.subplots(1, 2, figsize=(12, 6))
    im = ax[0].imshow(intensity, extent=[-bottom_size_mm/2, bottom_size_mm/2, -bottom_size_mm/2, bottom_size_mm/2],
                    origin='lower', cmap='inferno')
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


if __name__ == '__main__':
    
    # ground glass diffuser
    intensity = run_sim(
        square_law=False, 
        beer_lambert=False,
        num_points_bottom = 201, 
        num_points_interface = 201
    )
    plot_results(
        intensity,
        num_points_bottom=201
    )

    intensity = run_sim(beer_lambert=False)
    plot_results(intensity)

    intensity = run_sim(square_law=False)
    plot_results(intensity)

    intensity = run_sim()
    plot_results(intensity)

    intensity = run_sim(water_absorption_coefficient=1)
    plot_results(intensity)

    # air-water
    intensity = run_sim(n_glass=1.0, square_law=False, beer_lambert=False)
    plot_results(intensity)

    intensity = run_sim(n_glass=1.0)
    plot_results(intensity)

    # circular ground glass diffuser
    intensity = run_sim(boundaries=disk_boundaries)
    plot_results(intensity)

    intensity_air = run_sim(
        n_glass = 1.0, 
        glass_thickness = 6, 
        num_points_bottom = 201, 
        num_points_interface = 201, 
        boundaries = disk_boundaries, 
        glass_size_mm = 90
    )
    plot_results(intensity_air, num_points_bottom=201)

    # with a larger ground glass diffuser
    intensity_larger_diffuser = run_sim(glass_size_mm=100, bottom_size_mm=200)
    plot_results(intensity_larger_diffuser, bottom_size_mm=200)