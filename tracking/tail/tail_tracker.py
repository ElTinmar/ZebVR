from typing import List 
import numpy as np
from numpy.typing import NDArray
import cv2
import math 
from scipy.interpolate import splprep, splev
from core.abstractclasses import Tracker
from tracking.body.body_tracker import BodyTracker
import cv2

class TailTracker(Tracker):
    def __init__(
        self,
        threshold_body_intensity: float, 
        threshold_body_area: int,
        tail_length: float,
        n_tail_points: int = 10,
        ksize: int = 10,
        arc_angle_deg: float = 150,
        n_pts_interp: int = 40,
        n_pts_arc: int = 20,
        alpha: int = 100,
        color_heading: tuple = (0,0,1),
        color_tail: tuple = (1,0,1)
    ) -> None:
        
        super().__init__()
        self.body_tracker = BodyTracker(
            threshold_body_intensity, 
            threshold_body_area
        )
        self.tail_length = tail_length
        self.n_tail_points = n_tail_points
        self.ksize = ksize
        self.arc_angle_deg = arc_angle_deg
        self.n_pts_interp = n_pts_interp
        self.n_pts_arc = n_pts_arc

        # tracking
        self.skeleton = None
        self.skeleton_interp = None
        self.fish_centroid = None
        self.principal_components = None
        self.fish_mask = None

        # overlay parameters
        self.alpha = alpha
        self.color_heading = color_heading 
        self.color_tail = color_tail 

    def track(self, image: NDArray) -> List[NDArray]:

        [fish_centroid, principal_components, fish_mask] = self.body_tracker.track(image)

        if fish_centroid is not None:
            # apply a gaussian filter
            arc_rad = math.radians(self.arc_angle_deg)/2
            frame_blurred = cv2.boxFilter(image, -1, (self.ksize, self.ksize))
            spacing = float(self.tail_length) / self.n_tail_points
            # why the minus sign ?
            start_angle = math.pi + np.arctan2(-principal_components[1,0],principal_components[0,0]) 
            arc = np.linspace(-arc_rad, arc_rad, self.n_pts_arc) + start_angle
            x, y = fish_centroid
            points = [[x, y]]
            for j in range(self.n_tail_points):
                try:
                    # Find the x and y values of the arc centred around current x and y
                    xs = x + spacing * np.cos(arc)
                    ys = y - spacing * np.sin(arc)
                    # Convert them to integer, because of definite pixels
                    xs, ys = xs.astype(int), ys.astype(int)
                    # Find the index of the minimum or maximum pixel intensity along arc
                    idx = np.argmax(frame_blurred[ys, xs])
                    # Update new x, y points
                    x = xs[idx]
                    y = ys[idx]
                    # Create a new 180 arc centered around current angle
                    arc = np.linspace(arc[idx] - arc_rad, arc[idx] + arc_rad, self.n_pts_arc)
                    # Add point to list
                    points.append([x, y])
                except IndexError:
                    points.append(points[-1])

            # interpolate
            skeleton = np.array(points)
            tck, _ = splprep(skeleton.T)
            new_points = splev(np.linspace(0,1,self.n_pts_interp), tck)
            skeleton_interp = np.array([new_points[0],new_points[1]])
            
            self.skeleton = skeleton
            self.skeleton_interp = skeleton_interp.T
            self.fish_centroid = fish_centroid
            self.principal_components = principal_components
            self.fish_mask = fish_mask

            return [skeleton, skeleton_interp.T, fish_centroid, principal_components, fish_mask]
        else:
            self.skeleton = None
            self.skeleton_interp = None
            self.fish_centroid = None
            self.principal_components = None
            self.fish_mask = None
            
            return [None, None, None, None, None]
        
    def tracking_overlay(self, image: NDArray) -> NDArray:
        
        overlay = np.zeros(
            (image.shape[0],image.shape[1],3), 
            dtype=np.single
        )
        
        if self.fish_centroid is not None:
            pt1 = self.fish_centroid
            pt2 = self.fish_centroid + self.alpha*self.principal_components[:,0]
            overlay = cv2.line(
                overlay,
                pt1.astype(np.int32),
                pt2.astype(np.int32),
                self.color_heading
            )

            if self.skeleton_interp is not None:
                for pt1, pt2 in zip(self.skeleton_interp[:-1,],self.skeleton_interp[1:,]):
                    overlay = cv2.line(
                        overlay,
                        pt1.astype(np.int32),
                        pt2.astype(np.int32),
                        self.color_tail
                    )
        
        return overlay