import numpy as np
import matplotlib.pyplot as plt

# Parameters
total_time = 1_000
x0, y0 = 0.0, 0.0

# Arena size (rectangle)
Lx = 10  # half-width in x
Ly = 5   # half-height in y

# Dark region (x < 0)
dark_step_std = 1.0
dark_tau = 1.5

# Light region (x >= 0)
light_step_std = 1.5
light_tau = 0.5

# Initialize lists
time_in_dark = [0.0]
time_in_light = [0.0]

nreps = 100

for rep in range(nreps):

    x, y = x0, y0
    t = 0.0
    positions = [(x0, y0)]
    times = [0.0]
    time_in_dark.append(0.0)
    time_in_light.append(0.0)

    while t < total_time:
        # Choose parameters based on current x
        if x < 0:
            step_std = dark_step_std
            tau = dark_tau
        else:
            step_std = light_step_std
            tau = light_tau

        # Sample inter-event time
        dt = np.random.exponential(tau)

        # Keep sampling until move is within bounds
        while True:
            angle = np.random.uniform(0, 2 * np.pi)
            dx = np.random.normal(loc=0.0, scale=step_std) * np.cos(angle)
            dy = np.random.normal(loc=0.0, scale=step_std) * np.sin(angle)

            new_x = x + dx
            new_y = y + dy

            if -Lx <= new_x <= Lx and -Ly <= new_y <= Ly:
                break  # Accept move

        # Update position and time
        x, y = new_x, new_y
        t += dt

        if x < 0:
            time_in_dark[rep] += dt
        else:
            time_in_light[rep] += dt

        positions.append((x, y))
        times.append(t)


# Boxplot
fig, ax = plt.subplots(figsize=(6, 6))
ax.boxplot([time_in_dark, time_in_light], labels=['Dark', 'Light'], patch_artist=True,
           boxprops=dict(facecolor='gray'), medianprops=dict(color='red'))
ax.set_title('Time Spent in Dark vs Light Compartments')
ax.set_ylabel('Time (seconds)')
plt.grid(True, axis='y')
plt.savefig('time_spent_compartments')
plt.show()

## Plotting trajectory
# Convert to arrays
positions = np.array(positions)
x_vals, y_vals = positions[:, 0], positions[:, 1]

fig, ax = plt.subplots(figsize=(10, 6))
ax.add_patch(plt.Rectangle((-Lx, -Ly), Lx, 2 * Ly, color='black'))  # dark side
ax.add_patch(plt.Rectangle((0, -Ly), Lx, 2 * Ly, color='white', edgecolor='black'))
ax.plot(x_vals, y_vals, color='gray', linewidth=1)
plt.xlabel('X')
plt.ylabel('Y')
plt.grid(True)
plt.xlim([-Lx, Lx])
plt.ylim([-Ly, Ly])
plt.savefig('trajectory')
plt.show()

## Plotting distributions

n_samples = 10_000

# Sample distributions
inter_event_dark = np.random.exponential(dark_tau, n_samples)
inter_event_light = np.random.exponential(light_tau, n_samples)

# Step sizes (radial distances before applying angle)
step_dark = np.random.normal(0, dark_step_std, n_samples)
step_light = np.random.normal(0, light_step_std, n_samples)

# Directions
angles = np.random.uniform(0, 2 * np.pi, n_samples)

fig, axs = plt.subplots(1, 3, figsize=(18, 5))

# Inter-event time distributions
axs[0].hist(inter_event_dark, bins=100, alpha=0.6, label='Dark', density=True)
axs[0].hist(inter_event_light, bins=100, alpha=0.6, label='Light', density=True)
axs[0].set_title('Inter-Event Time Distribution')
axs[0].set_xlabel('Time (s)')
axs[0].set_ylabel('Probability Density')
axs[0].legend()

# Step size distributions
axs[1].hist(step_dark, bins=100, alpha=0.6, label='Dark', density=True)
axs[1].hist(step_light, bins=100, alpha=0.6, label='Light', density=True)
axs[1].set_title('Step Size Distribution')
axs[1].set_xlabel('Step (px)')
axs[1].set_ylabel('Probability Density')
axs[1].legend()

# Direction distribution
axs[2].hist(angles, bins=100, color='gray', density=True)
axs[2].set_title('Direction Distribution')
axs[2].set_xlabel('Angle (radians)')
axs[2].set_ylabel('Probability Density')

plt.tight_layout()
plt.savefig('mc_distribution')
plt.show()