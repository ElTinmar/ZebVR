import numpy as np

# Parameters
n_w = 1.33
n_g = 1.45
d = 5.0        # water depth
t = 1.6        # glass thickness
b = 25.0       # half-width of top boundary
num_points = 201

# Bottom points
x_b_array = np.linspace(-100, 100, num_points)
I_profile = np.zeros_like(x_b_array)

# Candidate angles for integration
theta_w_all = np.linspace(-np.pi/2, np.pi/2, 20000)

for i, x_b in enumerate(x_b_array):
    # Refraction
    theta_g_all = np.arcsin((n_w/n_g) * np.sin(theta_w_all))
    
    # Top position
    x_top = x_b + d*np.tan(theta_w_all) + t*np.tan(theta_g_all)
    
    # Apply top boundary
    mask = (x_top >= -b) & (x_top <= b)
    theta_valid = theta_w_all[mask]
    
    # Integrate intensity
    I_profile[i] = np.trapz(np.cos(theta_g_all[mask]), theta_valid)

# Normalize for plotting
I_profile /= I_profile.max()

# Plot
import matplotlib.pyplot as plt
plt.plot(x_b_array, I_profile)
plt.xlabel("x_b (mm)")
plt.ylabel("Normalized intensity")
plt.title("1D intensity profile along bottom (top boundary applied)")
plt.grid(True)
plt.show()

###

I = np.ones_like(x_b_array)
mask = (x_b_array >= -b) & (x_b_array <= b)
I[mask] = 1/I_profile[mask]
I_corrected = np.zeros_like(x_b_array)

for i, x_b in enumerate(x_b_array):
    # Refraction
    theta_g_all = np.arcsin((n_w/n_g) * np.sin(theta_w_all))
    
    # Top position
    x_top = x_b + d*np.tan(theta_w_all) + t*np.tan(theta_g_all)
    
    # Apply top boundary
    mask = (x_top >= -b) & (x_top <= b)
    theta_valid = theta_w_all[mask]
    
    # Integrate intensity
    I_corrected[i] = np.trapz(I[i]*np.cos(theta_g_all[mask]), theta_valid)

import matplotlib.pyplot as plt
plt.plot(x_b_array, I_profile)
plt.plot(x_b_array, I, color='r')
plt.plot(x_b_array, I_corrected,color='g')
plt.xlabel("x_b (mm)")
plt.ylabel("Normalized intensity")
plt.title("1D intensity profile along bottom (top boundary applied)")
plt.grid(True)
plt.show()



