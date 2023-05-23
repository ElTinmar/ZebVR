from typing import Tuple 
import numpy as np
from numpy.typing import NDArray
import cv2
import math 
from scipy.interpolate import splprep, splev


def tail_tracker(frame: NDArray,
        principal_components: NDArray,
        fish_centroid: NDArray,
        tail_length: float,
        n_tail_points: int = 10,
        ksize: int = 10,
        arc_angle_deg: float = 150,
        n_pts_interp = 40,
        n_pts_arc = 20
    ) -> Tuple[NDArray,NDArray]:

    """
    Track the tail of a single fish
    Input: 
        frame: single precision, grayscale image as numpy array
    Output:
        skeleton: skeleton of the tail 
    """
    
    # apply a gaussian filter
    arc_rad = math.radians(arc_angle_deg)/2
    frame_blurred = cv2.boxFilter(frame, -1, (ksize, ksize))
    spacing = float(tail_length) / n_tail_points
    # why ?
    start_angle = math.pi + np.arctan2(-principal_components[1,0],principal_components[0,0]) 
    arc = np.linspace(-arc_rad, arc_rad, n_pts_arc) + start_angle
    x, y = fish_centroid
    points = [[x, y]]
    for j in range(n_tail_points):
        try:
            # Find the x and y values of the arc centred around current x and y
            xs = x + spacing * np.cos(arc)
            ys = y - spacing * np.sin(arc)
            # Convert them to integer, because of definite pixels
            xs, ys = xs.astype(int), ys.astype(int)
            # Find the index of the minimum or maximum pixel intensity along arc
            idx = np.argmax(frame_blurred[ys, xs])
            
            """
            # debug
            if j==0:
                frame_display = frame_blurred.copy()
                point_disp = np.column_stack((xs,ys))
                for pt1,pt2 in zip(point_disp[:-1,],point_disp[1:,]):
                    frame_display = cv2.line(frame_display,pt1.astype(np.int32),pt2.astype(np.int32),255)
                cv2.imshow('debug',frame_display)
                cv2.waitKey(1)
            """

            # Update new x, y points
            x = xs[idx]
            y = ys[idx]
            # Create a new 180 arc centered around current angle
            arc = np.linspace(arc[idx] - arc_rad, arc[idx] + arc_rad, n_pts_arc)
            # Add point to list
            points.append([x, y])
        except IndexError:
            points.append(points[-1])

    # interpolate
    skeleton = np.array(points)
    tck, u = splprep(skeleton.T)
    new_points = splev(np.linspace(0,1,n_pts_interp), tck)
    skeleton_interp = np.array([new_points[0],new_points[1]])

    return (skeleton, skeleton_interp.T)