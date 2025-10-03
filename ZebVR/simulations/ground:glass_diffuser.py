import numpy as np
import matplotlib.pyplot as plt

# Parameters
glass_size = 50.0  # mm
glass_thcikness = 1.6 # mm
water_depth = 5.0  # mm
n_glass = 1.45
n_water = 1.33

# Grid at the bottom of water (larger than glass to capture spread)
grid_size = 50  # mm
num_points = 300
x = np.linspace(-grid_size/2, grid_size/2, num_points)
y = np.linspace(-grid_size/2, grid_size/2, num_points)
X, Y = np.meshgrid(x, y)

# Function to compute Lambertian intensity contribution from a point
def lambertian_intensity(x0, y0, X, Y, water_depth):
    dx = X - x0
    dy = Y - y0
    r = np.sqrt(dx**2 + dy**2 + water_depth**2)
    cos_theta = water_depth / r
    intensity = cos_theta / (r**2)  # inverse square + Lambertian
    return intensity

# Sample points on the glass diffuser (coarse grid)
num_sample = 20
points = np.linspace(-glass_size/2, glass_size/2, num_sample)
X_points, Y_points = np.meshgrid(points, points)
intensity_map = np.zeros_like(X)

# Sum contributions from all diffuser points
for xi, yi in zip(X_points.flatten(), Y_points.flatten()):
    intensity_map += lambertian_intensity(xi, yi, X, Y, water_depth)

# Normalize intensity to max=1
intensity_map /= intensity_map.max()

# Plot
plt.figure(figsize=(6,5))
plt.imshow(intensity_map, extent=[-grid_size/2, grid_size/2, -grid_size/2, grid_size/2],
           origin='lower', cmap='inferno')
plt.colorbar(label='Normalized intensity')
plt.title('Intensity profile at bottom of water (diffuse glass top)')
plt.xlabel('x (mm)')
plt.ylabel('y (mm)')
plt.show()
