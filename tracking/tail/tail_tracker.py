import numpy as np
from numpy.typing import NDArray
import cv2
import math 
from scipy.interpolate import splprep, splev
from core.abstractclasses import Tracker
from tracking.body.body_tracker import BodyTracker
import cv2
from core.dataclasses import TailTracking

class TailTracker(Tracker):
    def __init__(
        self,
        body_tracker: BodyTracker,
        dynamic_cropping_len_mm: float,
        pixels_per_mm: float,
        tail_length_mm: float = 3,
        n_tail_points: int = 10,
        ksize: int = 10,
        arc_angle_deg: float = 150,
        n_pts_interp: int = 40,
        n_pts_arc: int = 20,
        rescale: float = None
    ) -> None:
        
        super().__init__()
        self.body_tracker = body_tracker  
        self.n_tail_points = n_tail_points
        self.ksize = ksize
        self.arc_angle_deg = arc_angle_deg
        self.n_pts_interp = n_pts_interp
        self.n_pts_arc = n_pts_arc
        self.pixels_per_mm = pixels_per_mm
        self.tail_length_pix = tail_length_mm * pixels_per_mm
        self.dynamic_cropping_len_pix = dynamic_cropping_len_mm * pixels_per_mm
        self.rescale = rescale

        if rescale is not None:
            self.tail_length_pix *= rescale
            self.dynamic_cropping_len_pix *= rescale

    def track(self, image: NDArray) -> TailTracking:

        body_tracking = self.body_tracker.track(image)

        # tracking is faster on small images
        if self.rescale is not None:
            body_tracking.centroid *= self.rescale
            image = cv2.resize(
                    image, 
                    None, 
                    fx = self.rescale, 
                    fy = self.rescale,
                    interpolation=cv2.INTER_NEAREST
                )

        if body_tracking is not None:
            left = max(int(body_tracking.centroid[0]) - self.dynamic_cropping_len_pix, 0)
            right = min(int(body_tracking.centroid[0]) + self.dynamic_cropping_len_pix, image.shape[1])
            bottom = max(int(body_tracking.centroid[1]) - self.dynamic_cropping_len_pix, 0)
            top = min(int(body_tracking.centroid[1]) + self.dynamic_cropping_len_pix, image.shape[0])
            image = image[left:right,bottom:top]

            # apply a gaussian filter
            arc_rad = math.radians(self.arc_angle_deg)/2
            frame_blurred = cv2.boxFilter(image, -1, (self.ksize, self.ksize))
            spacing = float(self.tail_length_pix) / self.n_tail_points
            # why the minus sign ? maybe something with the location of the origin (topleft) vs arctan2 quadrant ?
            start_angle = math.pi + \
                np.arctan2(
                    -body_tracking.heading[1,0],
                    body_tracking.heading[0,0]
                ) 
            arc = np.linspace(-arc_rad, arc_rad, self.n_pts_arc) + start_angle
            x, y = body_tracking.centroid - [bottom, left]
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
            skeleton = np.array(points).astype('float') + [bottom, left]
            if self.rescale is not None:
                skeleton *= 1/self.rescale
            try:
                tck, _ = splprep(skeleton.T)
                new_points = splev(np.linspace(0,1,self.n_pts_interp), tck)
                skeleton_interp = np.array([new_points[0],new_points[1]])
                tail_points_interp = skeleton_interp.T
            except ValueError:
                tail_points_interp = None
                
            tracking = TailTracking(
                tail_points = skeleton,
                tail_points_interp = tail_points_interp,
                body = body_tracking
            )

            return tracking
        else:
            return None
        