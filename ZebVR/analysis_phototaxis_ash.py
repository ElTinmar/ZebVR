import matplotlib.patches
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.animation as animation
import numpy as np

## Visualization of the results --------------------------------------------------------------------

FILENAME = 'darkleft_Thu_04_Jul_2024_18h00min54sec.csv'

data = pd.read_csv(FILENAME)
data_filtered = data.groupby('image_index').first()
data_filtered = data_filtered[1:]

time = 1e-9*(data_filtered['t_display'] - data_filtered['t_display'].iloc[0])
time = time.values

## time
plt.plot(1/data['t_local'].diff())
plt.show()

plt.plot(1/np.diff(time))
plt.show()

## trajectories
plt.plot(data_filtered['centroid_x'],data_filtered['centroid_y'])
plt.axis('square')
plt.show()

## distance
x_diff = data_filtered['centroid_x'].diff()
y_diff = data_filtered['centroid_y'].diff()
distance = np.sqrt(x_diff**2+y_diff**2)

## bout detection 
distance_ewm = distance.ewm(alpha=0.05).mean()
bouts = 1*(distance_ewm > 5)
start = np.where(bouts.diff()>0)[0]
stop = np.where(bouts.diff()<0)[0]

fig = plt.figure() 
ax = fig.add_subplot(111) 
for x0,x1 in zip(start,stop):
    rect = matplotlib.patches.Rectangle((time[x0],0), time[x1]-time[x0], 100, color='lightgray')
    ax.add_patch(rect)
plt.plot(time,distance_ewm)
plt.plot(time,distance)
plt.show()

## angle
# positive angles: fish turning right
# negative angles: fish turning left
angle = np.arctan2(data_filtered['pc2_y'],data_filtered['pc2_x'])
angle_unwrapped = np.unwrap(angle) 
plt.plot(time,angle_unwrapped)
plt.show()

## animation with trajectories and angle
fig = plt.figure() 

ax0 = fig.add_subplot(311) 
angle_global = ax0.plot(time,angle_unwrapped)[0]
distance_global = ax0.plot(time,distance_ewm)[0]
location = ax0.plot([0, 0],[-200,200])[0]
ax0.set(ylim=[min(angle_unwrapped)-10, max(angle_unwrapped)+10])

ax1 = fig.add_subplot(312) 
pc2_x = np.array([data_filtered['centroid_x'].iloc[0], 
                  data_filtered['centroid_x'].iloc[0] + 100*data_filtered['pc2_x'].iloc[0]])
pc2_y = np.array([data_filtered['centroid_y'].iloc[0], 
                  data_filtered['centroid_y'].iloc[0] + 100*data_filtered['pc2_y'].iloc[0]])
trajectory_line = ax1.plot(data_filtered['centroid_x'].iloc[0],data_filtered['centroid_y'].iloc[0])[0]
orientation_line = ax1.plot(pc2_x,pc2_y)[0]
ax1.set(xlim=[0, 2048], ylim=[0, 2048])
ax1.axis('square')

ax2 = fig.add_subplot(313) 
angle_line = ax2.plot(time[0],angle_unwrapped[0])[0]
ax2.set(ylim=[min(angle_unwrapped)-10, max(angle_unwrapped)+10])


def update(frame, history:int = 250):
    angle_line.set_xdata(time[max(frame-history,0):frame])
    angle_line.set_ydata(angle_unwrapped[max(frame-history,0):frame])
    ax2.set(xlim=[time[frame]-5, time[frame]+1])

    trajectory_line.set_xdata(data_filtered['centroid_x'].iloc[max(frame-history,0):frame])
    trajectory_line.set_ydata(data_filtered['centroid_y'].iloc[max(frame-history,0):frame])
    pc2_x = np.array([data_filtered['centroid_x'].iloc[frame], 
                  data_filtered['centroid_x'].iloc[frame] + 100*data_filtered['pc2_x'].iloc[frame]])
    pc2_y = np.array([data_filtered['centroid_y'].iloc[frame], 
                  data_filtered['centroid_y'].iloc[frame] + 100*data_filtered['pc2_y'].iloc[frame]])
    orientation_line.set_xdata(pc2_x)
    orientation_line.set_ydata(pc2_y)
    ax1.set(xlim=[0, 2048], ylim=[0, 2048])

    location.set_xdata([time[frame], time[frame]])

    return (angle_line, trajectory_line, orientation_line, location)

ani = animation.FuncAnimation(fig=fig, func=update, frames=range(0,len(time),5), interval=200)
plt.show()

## Plotting 7dpf together

LEFT = True
RIGHT = False
FILENAME = [
    ('20240703_7dpf_LD_02_01.csv',LEFT,7),
    ('20240703_7dpf_RD_03_01.csv',RIGHT,7),
    ('20240703_7dpf_RD_04_01.csv',RIGHT,7),
    ('20240704_8dpf_LD_02_01.csv',LEFT,8),
    ('20240704_8dpf_LD_03_01.csv',LEFT,8),
    ('20240704_8dpf_RD_01_01.csv',RIGHT,8)
]
color = {LEFT: 'b', RIGHT: 'r'}

fig, ax = plt.subplots(1,2) 

for n, target_dpf in enumerate([7,8]):
    for filename, direction, age in FILENAME:
        if age == target_dpf:
            data = pd.read_csv(filename)
            data_filtered = data.groupby('image_index').first()
            data_filtered = data_filtered[1:]

            time = 1e-9*(data_filtered['t_display'] - data_filtered['t_display'].iloc[0])
            time = time.values

            angle = np.arctan2(data_filtered['pc2_y'],data_filtered['pc2_x'])
            angle_unwrapped = np.unwrap(angle) 
            ax[n].plot(time,angle_unwrapped, color=color[direction])

plt.show()

