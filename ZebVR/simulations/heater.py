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
