import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple

# References
# https://doi.org/10.3389/fphys.2023.1272366: 237.1 pmol.min-1 @ 5dpf ->
# https://doi.org/10.1152/ajpregu.1999.276.2.R505: 40 micromol.g-1.h-1 @ 10dpf for a 0.9g larva -> 36 nmol.h-1 -> 600 pmol.min-1

plt.rcParams['text.usetex'] = True

m_O2 = 32       # g/mol

# At 28C
oxygen_mg_L_init_mg_per_L = 7.75  # mg/L
carbon_dioxyde_init_mg_per_L = 0.6  # mg/L 
hypoxia_threshold_mg_per_L = 2.0   # mg/L (hypoxia threshold), https://doi.org/10.1101/2025.05.07.652688 (no change in OMR response at that level)

# Volume
well_radius_mm = 19.5/2
well_depth_mm = 5
well_volume_L = np.pi*well_depth_mm*well_radius_mm**2 * 1e-6

# Larval metabolism 
oxygen_consumption_pmols_per_min = 300
oxygen_consumption_mol_per_hr = oxygen_consumption_pmols_per_min * 1e-12 * 60  # mol/h
oxygen_consumption_mg_per_hr = oxygen_consumption_mol_per_hr * m_O2 * 1000     # mg/h
respiratory_quotient = 1.0                                                     

def gaz_concentration(
    oxygen_mg_L_init_mg_per_L: float,
    carbon_dioxyde_init_mg_per_L: float,
    oxygen_consumption_mg_per_hr: float,
    respiratory_quotient: float
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    
    dt_hr = 0.1 
    time_hr = [0.0]
    oxygen_mg_L = [oxygen_mg_L_init_mg_per_L]
    carbon_dioxyde_mg_L = [carbon_dioxyde_init_mg_per_L]

    while oxygen_mg_L[-1] > hypoxia_threshold_mg_per_L:
        delta_O2 = oxygen_consumption_mg_per_hr * dt_hr / well_volume_L
        oxygen_mg_L.append(oxygen_mg_L[-1] - delta_O2)
        carbon_dioxyde_mg_L.append(carbon_dioxyde_mg_L[-1] + delta_O2 * respiratory_quotient)
        time_hr.append(time_hr[-1] + dt_hr)

    time_hr = np.array(time_hr)
    oxygen_mg_L = np.array(oxygen_mg_L)
    carbon_dioxyde_mg_L = np.array(carbon_dioxyde_mg_L)

    return time_hr, oxygen_mg_L, carbon_dioxyde_mg_L

def plot(
    time_hr: np.ndarray,  
    oxygen_mg_L: np.ndarray, 
    carbon_dioxyde_mg_L: np.ndarray
):

    plt.figure(figsize=(8,5))
    plt.plot(time_hr, oxygen_mg_L, label='$O_2$', color='r')
    #plt.plot(time_hr, carbon_dioxyde_mg_L, '--', label='$CO_2$', color='k')
    plt.axhline(hypoxia_threshold_mg_per_L, color='red', linestyle=':', label='Hypoxia threshold')
    plt.xlabel('Time (h)')
    plt.ylabel('Concentration (mg/L)')
    plt.ylim(0,10)
    plt.title('$O_2$ Depletion')
    plt.legend()
    plt.grid(True)
    plt.savefig('ZebVR/simulations/oxygen.png')
    plt.show()

if __name__ == "__main__":

    time_hr, oxygen_mg_L, carbon_dioxyde_mg_L = gaz_concentration(    
        oxygen_mg_L_init_mg_per_L,
        carbon_dioxyde_init_mg_per_L,
        oxygen_consumption_mg_per_hr,
        respiratory_quotient
    )
    plot(time_hr, oxygen_mg_L, carbon_dioxyde_mg_L)
