import matplotlib.patches
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

FILENAME = '02072024_11dpf_LD__1_1.csv'

data = pd.read_csv(FILENAME)
data_filtered = data.groupby('image_index').first()
data_filtered = data_filtered[1:]

time = 1e-9*(data_filtered['t_display'] - data_filtered['t_display'].iloc[0])
time = time.values

# trajectories
plt.plot(data_filtered['centroid_x'],data_filtered['centroid_y'])
plt.axis('square')
plt.show()

# distance
x_diff = data_filtered['centroid_x'].diff()
y_diff = data_filtered['centroid_y'].diff()
distance = np.sqrt(x_diff**2+y_diff**2)

# bout detection 
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
plt.show()

# angle
angle = np.arctan2(data_filtered['pc2_y'],data_filtered['pc2_x'])
angle_unwrapped = np.unwrap(angle) 
plt.plot(time,angle_unwrapped)
plt.plot(time,angle)
plt.show()
