from utils.video_reader import OpenCV_VideoReader
import utils.background_model as bckg
import cv2
from utils.im2float import im2single
from utils.im2gray import im2gray
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from math import pi
import numpy as np
from body.body_tracker import body_tracker_PCA
from prey.prey_tracker import prey_tracker
from eyes.eyes_tracker import eyes_tracker
from tail.tail_tracker import tail_tracker
from prey.hungarian_assignment import ID_tracker

mov = OpenCV_VideoReader('toy_data/behavior_2000.avi',safe=False)

# Background model
sample = bckg.sample_frames_evenly(mov,500)
background = bckg.background_model_mode(sample)

# estimate the area in pixel of the fish by an ellipse
fish_length_mm = 6
fish_width_mm = 1
pixel_per_mm = 10
mm_per_pixel = 1/pixel_per_mm
est_fish_area_pixel = int(pi * fish_length_mm/2 * fish_width_mm/2 * pixel_per_mm**2)

# estimate threshold (do it once and don't put it in the function ?)
#sorted_pixel_values = bckg_sub_norm.ravel()
#sorted_pixel_values.sort()
#brightest_pixels = sorted_pixel_values[-est_fish_area_pixel:-1]

# Paramecia tracking

alpha = 100
threshold_intensity = 0.2
threshold_area = est_fish_area_pixel

threshold_intensity_eyes = 0.4
threshold_area_eye_min = 100
threshold_area_eye_max = 500

threshold_intensity_param = 0.025
threshold_area_param_min = 15
threshold_area_param_max = est_fish_area_pixel

dist_thresh = 20 
max_frames_to_skip = 50
max_trace_length = 10
trackIdCount = 100
tracker = ID_tracker(
    dist_thresh,
    max_frames_to_skip,
    max_trace_length,
    trackIdCount
)

mov.reset_reader()
while True:
    rval, frame = mov.next_frame()
    if not rval:
        break
    bckg_sub = abs(im2single(im2gray(frame)) - background)
    
    # track fish body
    fish_centroid, principal_components, _ = body_tracker_PCA(
        bckg_sub, 
        threshold_intensity, 
        threshold_area
    )
    
    # track paramecia
    prey_centroids, prey_mask = prey_tracker(
        bckg_sub,
        threshold_intensity_param,
        threshold_area_param_min,
        threshold_area_param_max
    )

    # hungarian assignment + kalman filter
    tracker.track(prey_centroids)

    # track eyes
    left_eye, right_eye, eye_mask = eyes_tracker(
        bckg_sub,
        threshold_intensity_eyes,
        threshold_area_eye_min,
        threshold_area_eye_max,
        principal_components,
        fish_centroid
    )

    # track tail
    ksize = 5
    tail_length = 160
    n_tail_points = 12
    arc_angle = 150
    n_pts_interp = 40
    tail_skeleton, tail_skeleton_interp  = tail_tracker(
        bckg_sub,
        principal_components,
        fish_centroid,
        tail_length,
        n_tail_points,
        ksize,
        arc_angle,
        n_pts_interp
    )

    # show tracking
    tracking = frame

    # body tracking
    if fish_centroid is not None:
        pt1 = fish_centroid
        pt2 = fish_centroid + alpha*principal_components[:,0]
        tracking = cv2.line(
            tracking,
            pt1.astype(np.int32),
            pt2.astype(np.int32),
            (0,0,255)
        )
        pt1 = fish_centroid
        pt2 = fish_centroid + alpha/2*principal_components[:,1]
        tracking = cv2.line(
            tracking,
            pt1.astype(np.int32),
            pt2.astype(np.int32),
            (0,0,0)
        )

    # eye tracking
    beta = 10
    if left_eye is not None:
        pt1 = left_eye.centroid
        pt2 = pt1 + beta*left_eye.direction
        tracking = cv2.line(
            tracking,
            pt1.astype(np.int32),
            pt2.astype(np.int32),
            (0,255,255)
        )
        pt2 = pt1 - beta*left_eye.direction
        tracking = cv2.line(
            tracking,
            pt1.astype(np.int32),
            pt2.astype(np.int32),
            (0,255,255)
        )
    if right_eye is not None:
        pt1 = right_eye.centroid
        pt2 = pt1 + beta*right_eye.direction
        tracking = cv2.line(
            tracking,
            pt1.astype(np.int32),
            pt2.astype(np.int32),
            (255,255,0)
        )
        pt2 = pt1 - beta*right_eye.direction
        tracking = cv2.line(
            tracking,
            pt1.astype(np.int32),
            pt2.astype(np.int32),
            (255,255,0)
        )

    # tail tracking
    for pt1, pt2 in zip(tail_skeleton_interp[:-1,],tail_skeleton_interp[1:,]):
        tracking = cv2.line(
            tracking,
            pt1.astype(np.int32),
            pt2.astype(np.int32),
            (255,0,255)
        )

    # prey tracking
    tracking = tracker.show_tracks(tracking)
    #for prey_loc in prey_centroids:
    #    tracking = cv2.circle(tracking,prey_loc.astype(np.int32),10,(0,255,0))

    cv2.imshow('Tracking', tracking)
    key = cv2.waitKey(1)
    if key == ord('q'):
        break
    
cv2.destroyAllWindows()
