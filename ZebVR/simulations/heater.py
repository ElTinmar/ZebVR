import numpy as np
import matplotlib.pyplot as plt

# Lumped-element model with Newton's law of cooling

# Geometry (m)
L = 0.55
W = 0.55
H = 0.75
V = L * W * H
# Wall thickness (m)
t_al    = 0.01
t_pm    = 0.005
# Areas of walls (m2)
A_al    = W * L                  # aluminium side area               
A_pm    = 4 * (L * H) + A_al     # total acrylic area 
A_loss  = A_al + A_pm

# Material properties
rho_al  = 2700.0   # kg/m3
cp_al   = 900.0    # J/(kg·K)
rho_pm  = 1200.0   # kg/m3
cp_pm   = 1450.0   # J/(kg·K)
rho_air = 1.2      # kg/m3
cp_air  = 1005.0   # J/(kg·K)

# Mass of wall materials
m_al    = rho_al * A_al * t_al
m_pm    = rho_pm * A_pm * t_pm
m_air   = rho_air * V

# Lumped heat capacity
C_tot   = m_al*cp_al + m_pm*cp_pm + m_air*cp_air

# Heater power (W)
P_heater = 75.0

# Ambient
T_amb = 20.0 + 273.15   # K

# Heat‐loss coefficient (global) W/(m2·K)
h       = 7.0           # NEED TO GET THIS RIGHT !

# Time‐integration parameters
dt      = 1.0           # s
t_end   = 3600*2        # simulate 2 hours
n_steps = int(t_end/dt)
times   = np.arange(0, t_end+dt, dt)
T       = np.zeros_like(times)
T[0]    = T_amb

for i in range(1, len(times)):
    # current temp
    T_cur = T[i-1]
    # input minus loss
    Q_in  = P_heater
    Q_loss= h * A_loss * (T_cur - T_amb)
    dTdt  = (Q_in - Q_loss) / C_tot
    T[i] = T_cur + dTdt * dt

# Convert K to °C
T_C = T - 273.15

# Plot
plt.figure()
plt.plot(times/60.0, T_C)
plt.xlabel('Time (minutes)')
plt.ylabel('Interior Temperature (°C)')
plt.grid(True)
plt.show()


####################

import numpy as np
from scipy.optimize import fsolve

# --- 1. Define Thermal Constants and Known Parameters ---

# Internal Heat Generation (Qin)
Q_in = 75.0  # Watts

# Material Properties (Acrylic)
k_acrylic = 0.2          # Thermal conductivity of acrylic [W/(m*K)]
epsilon_acrylic = 0.9    # Emissivity of acrylic (high for non-metals)

# Heat Transfer Coefficients (Estimated for Natural Convection)
h_conv = 8.0             # Estimated natural convection coefficient to ambient air [W/(m^2*K)]
                         # (Typical range for still air is 5-10 W/(m^2*K))

# Ambient Conditions
T_ambient_C = 20.0       # Ambient temperature [°C]
T_ambient_K = T_ambient_C + 273.15  # Convert to Kelvin [K] (required for radiation)
T_surr_K = T_ambient_K   # Assume surrounding temperature (T_surr) equals T_ambient

# Physical Constants
sigma = 5.67e-8          # Stefan-Boltzmann constant [W/(m^2*K^4)]

# --- 2. Input Enclosure Dimensions (Example Case) ---

# Dimensions (in meters)
L = 0.55                 # Length [m] 
W = 0.55                 # Width [m] 
H = 0.75                 # Height [m] 
wall_thickness = 0.005   # Wall thickness (Delta x) [m] (5 mm)

# --- 3. Geometric Calculations ---

def calculate_surface_area(L, W, H):
    """Calculates the total external surface area of a rectangular enclosure."""
    # Area = 2 * (LW + LH + WH)
    Area = 2 * (L * W + L * H + W * H)
    return Area

Area = calculate_surface_area(L, W, H)
print(f"--- Enclosure Geometry ---")
print(f"Total External Surface Area (A): {Area:.3f} m^2")
print(f"Wall Thickness (Δx): {wall_thickness*1000:.1f} mm")

# --- 4. Define the Governing Heat Loss Equation ---

def heat_loss_residual(T_surf_K):
    """
    Function representing the energy balance (Q_loss - Q_in = 0).
    We solve for T_surf_K that makes this function zero.
    """
    # Q_convection = h_conv * A * (T_surf - T_ambient)
    Q_conv = h_conv * Area * (T_surf_K - T_ambient_K)

    # Q_radiation = epsilon * sigma * A * (T_surf^4 - T_surr^4)
    Q_rad = epsilon_acrylic * sigma * Area * (T_surf_K**4 - T_surr_K**4)

    Q_loss = Q_conv + Q_rad

    # Residual = Q_loss - Q_in (This should be zero at steady state)
    residual = Q_loss - Q_in
    return residual

# --- 5. Solve the System for Steady-State Surface Temperature (T_surf) ---

# Initial guess for the surface temperature (slightly higher than ambient)
T_surf_guess_K = T_ambient_K 

# Use fsolve to find the root (T_surf_K where the residual is zero)
T_surf_steady_K = fsolve(heat_loss_residual, T_surf_guess_K)[0]
T_surf_steady_C = T_surf_steady_K - 273.15

# --- 6. Calculate Inner Air Temperature (T_int) ---

# At steady state, Q_in is conducted through the wall
Q_cond = Q_in
R_cond = wall_thickness / (k_acrylic * Area)  # Thermal resistance of the wall [K/W]

# Conduction equation: Q_cond = (T_int - T_surf) / R_cond
# Rearranging for T_int: T_int = T_surf + Q_cond * R_cond
T_int_steady_K = T_surf_steady_K + Q_in * R_cond
T_int_steady_C = T_int_steady_K - 273.15

# --- 7. Output Results and Verification ---

# Recalculate Q_conv and Q_rad using the solved T_surf for verification
Q_conv_solved = h_conv * Area * (T_surf_steady_K - T_ambient_K)
Q_rad_solved = epsilon_acrylic * sigma * Area * (T_surf_steady_K**4 - T_surr_K**4)

print(f"\n--- Simulation Parameters ---")
print(f"Internal Heat Source (Q_in): {Q_in} W")
print(f"Ambient Temperature (T_amb): {T_ambient_C:.1f} °C")
print(f"Convection Coeff (h_conv): {h_conv:.1f} W/(m^2*K)")

print(f"\n--- Steady-State Results ---")
print(f"Outer Surface Temperature (T_surf): {T_surf_steady_C:.2f} °C ({T_surf_steady_K:.2f} K)")
print(f"Inner Air Temperature (T_int): {T_int_steady_C:.2f} °C ({T_int_steady_K:.2f} K)")
print(f"Temperature Rise (ΔT_rise): {T_int_steady_C - T_ambient_C:.2f} K")

print(f"\n--- Heat Loss Breakdown (Total = {Q_in} W) ---")
print(f"Convective Heat Loss (Q_conv): {Q_conv_solved:.2f} W")
print(f"Radiative Heat Loss (Q_rad): {Q_rad_solved:.2f} W")
print(f"Total Calculated Loss (Q_loss): {Q_conv_solved + Q_rad_solved:.2f} W (Matches Q_in)")
print(f"Wall Conductive Resistance (R_cond): {R_cond:.4f} K/W")