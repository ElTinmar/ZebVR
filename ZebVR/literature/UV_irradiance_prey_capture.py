# Kahn et al. https://www.sciencedirect.com/science/article/pii/S2666166723007475
# 15 nW 4 deg dot at 1.5mm

import numpy as np

dot_power_microwatts = 15*10**-3
dot_angle_size_deg = 4
half_angle_rad = np.deg2rad(dot_angle_size_deg/2)
d_cm = 0.15
r_cm = d_cm * np.tan(half_angle_rad)
dot_area_cm2 = np.pi*r_cm**2
irradiance_microW_cm2 = dot_power_microwatts / dot_area_cm2

print(f"irradiance: {irradiance_microW_cm2:.2f} \u03bcW/cm\u00b2")