import numpy as np 
import cv2
from numpy.typing import NDArray
from core.abstractclasses import Camera, Projector
from typing import List
import cv2

# TODO warn if there is substantial shearing/deformations that 
# the projector is not well aligned

class Cam2ProjReg:
    def __init__(
        self,
        camera: Camera,
        projector: Projector,
        num_frames_per_pt: int = 10, 
        grid_size_x: int = 10,
        grid_size_y: int = 10, 
        dot_radius: int = 5,
        dot_intensity: int = 255,
        ksize: int = 10
    ) -> None:
        
        self.camera = camera
        self.projector = projector
        self.num_frames_per_pt = num_frames_per_pt
        self.grid_size_x = grid_size_x
        self.grid_size_y = grid_size_y
        self.dot_radius = dot_radius
        self.dot_intensity = dot_intensity
        self.ksize = ksize

    def registration(self) -> List[NDArray]:

        cv2.namedWindow('registration')

        proj_size = self.projector.get_resolution()
        (width,height) = self.camera.get_resolution()

        xx,yy = np.meshgrid(range(proj_size[0]),range(proj_size[1]))

        x_start = round(proj_size[0]/(self.grid_size_x+1))
        x_step = x_start
        x_stop = (self.grid_size_x+1)*x_step
        y_start = round(proj_size[1]/(self.grid_size_y+1))
        y_step = y_start
        y_stop = (self.grid_size_y+1)*y_step

        self.camera.start_acquisition()

        count = 0
        coords_cam = np.zeros((self.grid_size_x*self.grid_size_y,2), dtype=np.single)
        coords_proj = np.zeros((self.grid_size_x*self.grid_size_y,2), dtype=np.single)
        for x in range(x_start,x_stop,x_step):
            for y in range(y_start,y_stop,y_step):
                # project a dot at (x,y)
                indices = (xx-x)**2 + (yy-y)**2 <= self.dot_radius**2
                dot = np.zeros((proj_size[1],proj_size[0]) , dtype=np.uint8)
                dot[indices] = self.dot_intensity
                self.projector.project(dot)

                # average over a few frames
                image = np.zeros((height,width), dtype=np.single)
                for frame in range(self.num_frames_per_pt):
                    data, res = self.camera.fetch()
                    img_data = data.get_img()
                    image = image + img_data/self.num_frames_per_pt
                    data.reallocate()

                # detect x,y position on camera sensor
                image = cv2.blur(image, (self.ksize, self.ksize))
                x_cam,y_cam = np.unravel_index(np.argmax(image), image.shape)

                # show detected points
                detected_spot = cv2.circle(image,(x_cam,y_cam),10,0,1)
                cv2.imshow('registration', detected_spot)
                cv2.waitKey(1)
                
                # store in numpy array
                coords_proj[count,:] = [x,y]
                coords_cam[count,:] = [x_cam,y_cam] 
                count += 1

        self.camera.stop_acquisition()

        cv2.destroyWindow('registration')

        # Use homogeneous coordinates to get affine transform
        coords_proj = np.append(
            coords_proj, 
            np.ones((self.grid_size_x*self.grid_size_y,1)),
            axis=1
        )
        coords_cam = np.append(
            coords_cam, 
            np.ones((self.grid_size_x*self.grid_size_y,1)),
            axis=1
        )
        
        try:
            Affine_proj2cam, _, _, _ = np.linalg.lstsq(coords_proj,coords_cam)
            Affine_cam2proj, _, _, _ = np.linalg.lstsq(coords_cam,coords_proj)
        except:
            print("Not enough points for registration, using identity")
            Affine_proj2cam = np.eye(3)
            Affine_cam2proj = np.eye(3)

        return Affine_cam2proj, Affine_proj2cam