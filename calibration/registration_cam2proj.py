import numpy as np 
import cv2

# TODO that function is big, maybe you can subdivide it further.
# That could also allow different calibration patterns to be used
# TODO warn if there is substantial shearing/deformations that 
# the projector is not well aligned

def calibration(
    cam, 
    num_frames_per_pt = 10, 
    wdw_offset = (0,0),
    grid_size = (10,10), 
    proj_size = (1140,912),
    dot_radius = 5,
    dot_intensity = 255,
    ksize = (10,10)
    ):
    """
    Project points on a grid and detect them on camera in order 
    to obtain an affine registration between camera and projector
    spaces
    """

    cv2.namedWindow("Calibration", cv2.WINDOW_FULLSCREEN)
    cv2.moveWindow("Calibration", wdw_offset[0], wdw_offset[1])

    dot = np.zeros(proj_size, dtype=np.uint8)
    xx,yy = np.meshgrid(range(proj_size[1]),range(proj_size[0]))

    x_start = round(proj_size[0]/(grid_size[0]+1))
    x_step = x_start
    x_stop = (grid_size[0]+1)*x_step
    y_start = round(proj_size[1]/(grid_size[1]+1))
    y_step = y_start
    y_stop = (grid_size[1]+1)*y_step

    height = cam.get_height()
    width = cam.get_width()
    image = np.zeros((height*width), dtype=np.single)

    cam.start_acquisition()

    count = 0
    coords_cam = np.zeros((grid_size[0]*grid_size[1],2), dtype=np.single)
    coords_proj = np.zeros((grid_size[0]*grid_size[1],2), dtype=np.single)
    for x in range(x_start,x_stop,x_step):
        for y in range(y_start,y_stop,y_step):

            # project a dot at (x,y)
            indices = (xx-x)**2 + (yy-y)**2 <= dot_radius**2
            dot[indices] = dot_intensity
            cv2.imshow(dot)
            cv2.waitKey()

            # average over a few frames
            for frame in range(num_frames_per_pt):
                buffer = cam.fetch()
                img_data = np.ndarray(
                    (height*width), 
                    dtype=np.single, 
                    buffer= 1/256 * buffer.get_img()
                )
                image = image + img_data/num_frames_per_pt
                buffer.queue()

            # detect x,y position on camera sensor
            image = cv2.blur(image, ksize)
            x_cam,y_cam = np.unravel_index(np.argmax(image), image.shape)

            # store in numpy array
            coords_proj[count,:] = [x,y]
            coords_cam[count,:] = [x_cam,y_cam] 
            count += 1

    cam.stop_acquisition()

    # Use homogeneous coordinates to get affine transform
    coords_proj = np.append(coords_proj, np.ones((grid_size[0]*grid_size[1],1)),axis=1)
    coords_cam = np.append(coords_cam, np.ones((grid_size[0]*grid_size[1],1)),axis=1)
    Affine_proj2cam, _, _, _ = np.linalg.lstsq(coords_proj,coords_cam)
    Affine_cam2proj, _, _, _ = np.linalg.lstsq(coords_cam,coords_proj)

    return Affine_cam2proj, Affine_proj2cam

