from core.abstractclasses import TrackerDisplay
from core.dataclasses import (
    Tracking, BodyTracking, EyeTracking, 
    TailTracking, PreyTracking, TrackingCollection,
    EyeParam
)
import cv2
from numpy.typing import NDArray
import numpy as np

class TrackerDisp(TrackerDisplay):
    def __init__(
            self, 
            pixels_per_mm: float,
            heading_len_mm: float = 2,
            eye_len_mm: float = 0.2,
            circle_radius_mm: float = 0.4, 
            color_heading: tuple = (0,0,1),
            color_eye_left: tuple = (0,1,1),
            color_eye_right: tuple = (1,1,0),
            color_tail: tuple = (1,0,1),
            circle_color: tuple = (0,1,0),
            rescale: float = None
        ) -> None:
        
        super().__init__()

        self.heading_len_pix = heading_len_mm * pixels_per_mm
        self.eye_len_pix = eye_len_mm * pixels_per_mm
        self.circle_radius_pix = int(circle_radius_mm * pixels_per_mm)
        self.color_heading = color_heading
        self.color_eye_left = color_eye_left
        self.color_eye_right = color_eye_right
        self.color_tail = color_tail 
        self.circle_color = circle_color
        self.pixels_per_mm = pixels_per_mm
        self.rescale = rescale

        if self.rescale is not None:
            self.heading_len_pix *= rescale
            self.eye_len_pix *= rescale
            self.circle_radius_pix *= rescale

    def display_body(self, parameters: BodyTracking) -> NDArray:

        tracking_image = np.dstack(
            (parameters.image,
             parameters.image,
             parameters.image)
        )
        
        if parameters is not None:
            pt1 = parameters.centroid
            pt2 = parameters.centroid + self.heading_len_pix*parameters.heading[:,0]
            tracking_image = cv2.line(
                tracking_image,
                pt1.astype(np.int32),
                pt2.astype(np.int32),
                self.color_heading
            )

        cv2.imshow('tracking',tracking_image)

    def display_eyes(self, parameters: EyeTracking) -> NDArray:
        
        def disp_eye(image: NDArray, eye: EyeParam, color):
            pt1 = eye.centroid
            pt2 = pt1 + self.eye_len_pix * eye.direction
            image = cv2.line(
                image,
                pt1.astype(np.int32),
                pt2.astype(np.int32),
                color
            )
            pt2 = pt1 - self.eye_len_pix * eye.direction
            image = cv2.line(
                image,
                pt1.astype(np.int32),
                pt2.astype(np.int32),
                color
            )
            return image

        tracking_image = np.dstack(
            (parameters.image,
             parameters.image,
             parameters.image)
        )

        if parameters is not None:
            if parameters.left_eye is not None:
                tracking_image = disp_eye(tracking_image, parameters.left_eye, self.color_eye_left)
            if parameters.right_eye is not None:
                tracking_image = disp_eye(tracking_image, parameters.right_eye, self.color_eye_right)

        cv2.imshow('eyes',tracking_image)

    def display_tail(self, parameters: TailTracking) -> NDArray:

        tracking_image = np.dstack(
            (parameters.image,
             parameters.image,
             parameters.image)
        )
        
        if parameters is not None:
            if parameters.tail_points_interp is not None:
                tail_segments = zip(
                    parameters.tail_points_interp[:-1,],
                    parameters.tail_points_interp[1:,]
                )
                for pt1, pt2 in tail_segments:
                    tracking_image = cv2.line(
                        tracking_image,
                        pt1.astype(np.int32),
                        pt2.astype(np.int32),
                        self.color_tail
                    )
        
        cv2.imshow('tail', tracking_image)

    def display_prey(self, parameters: PreyTracking) -> NDArray:

        tracking_image = np.dstack(
            (parameters.image,
             parameters.image,
             parameters.image)
        )

        for prey_loc in parameters.prey_centroids:
            tracking_image = cv2.circle(
                tracking_image, 
                prey_loc.astype(np.int32),
                self.circle_radius_pix,
                self.circle_color
            )

        cv2.imshow('prey', tracking_image)

    def display_collection(self, parameters: TrackingCollection) -> NDArray:
        
        if parameters.body is not None:
            self.display_body(parameters.body)
        if parameters.eyes is not None:
            self.display_eyes(parameters.eyes)
        if parameters.tail is not None:
            self.display_tail(parameters.tail)
        if parameters.prey is not None:
            self.display_prey(parameters.prey)
    
    def init_window(self):
        cv2.namedWindow('tracking')
        cv2.namedWindow('eyes')
        cv2.namedWindow('tail')
        cv2.namedWindow('prey')

    def close_window(self):
        cv2.destroyWindow('tracking')
        cv2.destroyWindow('eyes')
        cv2.destroyWindow('tail')
        cv2.destroyWindow('prey')

    def display(self, parameters: Tracking):
        if isinstance(parameters, BodyTracking):
            self.display_body(parameters)
        elif isinstance(parameters, EyeTracking):
            self.display_eyes(parameters)
        elif isinstance(parameters, TailTracking):
            self.display_tail(parameters)
        elif isinstance(parameters, PreyTracking):
            self.display_prey(parameters)
        elif isinstance(parameters, TrackingCollection):
            self.display_collection(parameters) 
        else:
            raise(TypeError("Unknown tracking type"))
        
        cv2.waitKey(1)
