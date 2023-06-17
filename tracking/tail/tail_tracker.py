import numpy as np
from numpy.typing import NDArray
import cv2
import math 
from scipy.interpolate import splprep, splev
from core.abstractclasses import Tracker
from tracking.body.body_tracker import BodyTracker
from core.dataclasses import TailTracking, Rect
from tracking.utils.diagonal_imcrop import diagonal_crop
from typing import Tuple

class TailTracker(Tracker):
    def __init__(
        self,
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
        self.n_tail_points = n_tail_points
        self.ksize = ksize
        self.arc_angle_deg = arc_angle_deg
        self.n_pts_interp = n_pts_interp
        self.n_pts_arc = n_pts_arc
        self.pixels_per_mm = pixels_per_mm
        self.tail_length_pix = tail_length_mm * pixels_per_mm
        self.dynamic_cropping_len_pix = int(np.ceil(dynamic_cropping_len_mm * pixels_per_mm))
        self.rescale = rescale

        if rescale is not None:
            self.tail_length_pix *= rescale

    @staticmethod
    def track_tail(
        image: NDArray,
        arc_angle_deg: float,
        ksize: int,
        n_tail_points: int,
        tail_length_pix: int,
        n_pts_arc: int,
        n_pts_interp: int
        ) -> Tuple[NDArray, NDArray]:

        # apply a gaussian filter
        arc_rad = math.radians(arc_angle_deg)/2
        frame_blurred = cv2.boxFilter(image, -1, (ksize, ksize))
        spacing = float(tail_length_pix) / n_tail_points
        arc = np.linspace(-arc_rad, arc_rad, n_pts_arc)
        x, y = [0, 0]
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
        skeleton = np.array(points).astype('float')
        try:
            tck, _ = splprep(skeleton.T)
            new_points = splev(np.linspace(0,1,n_pts_interp), tck)
            skeleton_interp = np.array([new_points[0],new_points[1]])
            tail_points_interp = skeleton_interp.T
        except ValueError:
            tail_points_interp = None
            
        return (skeleton, tail_points_interp)
    
    def track(
            self, 
            image: NDArray,
            centroid: NDArray, 
            heading: NDArray
        ) -> TailTracking:

        angle = np.arctan2(heading[1,1],heading[0,1]) 
        corner = centroid - 100 * heading[:,1] + 0 * heading[:,0]
        image_tail = diagonal_crop(
            image, 
            Rect(corner[0],corner[1],200,200),
            np.rad2deg(angle)
        )
        cv2.namedWindow('tail')
        cv2.imshow('tail', image_tail)
        cv2.waitKey(1)

        tail, tail_interp = TailTracker.track_tail(
            image_tail,
            self.arc_angle_deg,
            self.ksize,
            self.n_tail_points,
            self.tail_length_pix,
            self.n_pts_arc,
            self.n_pts_interp
        )

        tracking = TailTracking(
            tail_points = tail,
            tail_points_interp = tail_interp,
            heading = heading,
            centroid = centroid,
            image = image_tail
        )

        return tracking
        
        