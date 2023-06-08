from core.abstractclasses import TrackerDisplay
from core.dataclasses import Tracking, BodyTracking, EyeTracking, TailTracking, PreyTracking, TrackingCollection
import cv2
from numpy.typing import NDArray
import numpy as np

class TrackerDisp(TrackerDisplay):
    def __init__(
            self, 
            name: str,
            alpha: int = 100,
            beta: int = 10,
            circle_radius: int = 10, 
            color_heading: tuple = (0,0,1),
            color_eye_left: tuple = (0,1,1),
            color_eye_right: tuple = (1,1,0),
            color_tail: tuple = (1,0,1),
            circle_color: tuple = (0,1,0),
            rescale: float = None
        ) -> None:
        
        super().__init__()

        self.name = name
        self.alpha = alpha
        self.beta = beta
        self.color_heading = color_heading
        self.color_eye_left = color_eye_left
        self.color_eye_right = color_eye_right
        self.color_tail = color_tail 
        self.circle_radius = circle_radius
        self.circle_color = circle_color
        self.rescale = rescale

    def overlay_body(self, parameters: BodyTracking, image: NDArray) -> NDArray:

        overlay = np.zeros(
            (image.shape[0],image.shape[1],3), 
            dtype=np.single
        )
        
        if parameters is not None:
            pt1 = parameters.centroid
            pt2 = parameters.centroid + self.alpha*parameters.heading[:,0]
            overlay = cv2.line(
                overlay,
                pt1.astype(np.int32),
                pt2.astype(np.int32),
                self.color_heading
            )

        return overlay

    def overlay_eyes(self, parameters: EyeTracking, image: NDArray) -> NDArray:
        
        overlay = np.zeros(
            (image.shape[0],image.shape[1],3), 
            dtype=np.single
        )

        if parameters is not None:

            pt1 = parameters.body.centroid
            pt2 = parameters.body.centroid + \
                self.alpha * parameters.body.heading[:,0]
            overlay = cv2.line(
                overlay,
                pt1.astype(np.int32),
                pt2.astype(np.int32),
                self.color_heading
            )

            if parameters.left_eye is not None:
                pt1 = parameters.left_eye.centroid
                pt2 = pt1 + self.beta * parameters.left_eye.direction
                overlay = cv2.line(
                    overlay,
                    pt1.astype(np.int32),
                    pt2.astype(np.int32),
                    self.color_eye_left
                )
                pt2 = pt1 - self.beta * parameters.left_eye.direction
                overlay = cv2.line(
                    overlay,
                    pt1.astype(np.int32),
                    pt2.astype(np.int32),
                    self.color_eye_left
                )

            if parameters.right_eye is not None:
                pt1 = parameters.right_eye.centroid
                pt2 = pt1 + self.beta * parameters.right_eye.direction
                overlay = cv2.line(
                    overlay,
                    pt1.astype(np.int32),
                    pt2.astype(np.int32),
                    self.color_eye_right
                )
                pt2 = pt1 - self.beta * parameters.right_eye.direction
                overlay = cv2.line(
                    overlay,
                    pt1.astype(np.int32),
                    pt2.astype(np.int32),
                    self.color_eye_right
                )

        return overlay

    def overlay_tail(self, parameters: TailTracking, image: NDArray) -> NDArray:

        overlay = np.zeros(
            (image.shape[0],image.shape[1],3), 
            dtype=np.single
        )
        
        if parameters is not None:
            pt1 = parameters.body.centroid
            pt2 = parameters.body.centroid + \
                self.alpha * parameters.body.heading[:,0]
            overlay = cv2.line(
                overlay,
                pt1.astype(np.int32),
                pt2.astype(np.int32),
                self.color_heading
            )

            if parameters.tail_points_interp is not None:
                tail_segments = zip(
                    parameters.tail_points_interp[:-1,],
                    parameters.tail_points_interp[1:,]
                )
                for pt1, pt2 in tail_segments:
                    overlay = cv2.line(
                        overlay,
                        pt1.astype(np.int32),
                        pt2.astype(np.int32),
                        self.color_tail
                    )
        
        return overlay

    def overlay_prey(self, parameters: PreyTracking, image: NDArray) -> NDArray:

        overlay = np.zeros(
            (image.shape[0],image.shape[1],3), 
            dtype=np.single
        )

        for prey_loc in parameters.prey_centroids:
            overlay = cv2.circle(
                overlay, 
                prey_loc.astype(np.int32),
                self.circle_radius,
                self.circle_color
            )

        return overlay

    def overlay_collection(self, parameters: TrackingCollection, image: NDArray) -> NDArray:
        overlay = np.zeros(
            (image.shape[0],image.shape[1],3), 
            dtype=np.single
        )
        
        if parameters.body is not None:
            overlay += self.overlay_body(parameters.body, image)
        if parameters.eyes is not None:
            overlay += self.overlay_eyes(parameters.eyes,image)
        if parameters.tail is not None:
            overlay += self.overlay_tail(parameters.tail,image)
        if parameters.prey is not None:
            overlay += self.overlay_prey(parameters.prey,image)
        
        return overlay

    def overlay(self, parameters: Tracking, image: NDArray) -> NDArray:
        if isinstance(parameters, BodyTracking):
            return self.overlay_body(parameters, image)
        elif isinstance(parameters, EyeTracking):
            return self.overlay_eyes(parameters, image)
        elif isinstance(parameters, TailTracking):
            return self.overlay_tail(parameters, image)
        elif isinstance(parameters, PreyTracking):
            return self.overlay_prey(parameters, image)
        elif isinstance(parameters, TrackingCollection):
            return self.overlay_collection(parameters, image) 
        else:
            raise(TypeError("Unknown tracking type"))

    def init_window(self):
        cv2.namedWindow(self.name)

    def close_window(self):
        cv2.destroyWindow(self.name)

    def display(self, parameters: Tracking, image: NDArray):
        overlay = self.overlay(parameters, image)
        for c in range(overlay.shape[2]):
            overlay[:,:,c] = overlay[:,:,c] + image
        if self.rescale is not None:
            smallimg = cv2.resize(
                overlay, 
                None, 
                fx = self.rescale, 
                fy = self.rescale, 
                interpolation=cv2.INTER_LINEAR
            )
            cv2.imshow(self.name, smallimg)
        else:
            cv2.imshow(self.name, overlay)
        cv2.waitKey(1)