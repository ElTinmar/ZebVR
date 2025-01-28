import time
import numpy as np 
import os
from dagline import WorkerNode

class TrackingSaver(WorkerNode):

    def __init__(
            self, 
            filename: str = 'tracking.csv',
            num_tail_points_interp: int = 40,
            *args, 
            **kwargs
        ) -> None:

        super().__init__(*args, **kwargs)

        self.filename = filename
        self.num_tail_points_interp = num_tail_points_interp
        self.fd = None

    def set_filename(self, filename:str):
        self.filename = filename

    def initialize(self):
        super().initialize()
        
        # init file name
        prefix, ext = os.path.splitext(self.filename)
        file = prefix + time.strftime('_%a_%d_%b_%Y_%Hh%Mmin%Ssec') + ext
        while os.path.exists(file):
            time.sleep(1)
            file = prefix + time.strftime('_%a_%d_%b_%Y_%Hh%Mmin%Ssec') + ext

        # write csv headers
        self.fd = open(file, 'w')
        headers = (
            'image_index',
            'time',
            'centroid_x',
            'centroid_y',
            'pc1_x',
            'pc1_y',
            'pc2_x',
            'pc2_y',
            'left_eye_x',
            'left_eye_y',
            'left_eye_angle',
            'right_eye_x',
            'right_eye_y',
            'right_eye_angle',
        ) \
        + tuple(f'tail_point_{n:03d}_x' for n in range(self.num_tail_points_interp)) \
        + tuple(f'tail_point_{n:03d}_y' for n in range(self.num_tail_points_interp))
        self.fd.write(','.join(headers) + '\n')

    def cleanup(self):
        super().cleanup()
        self.fd.close()

    def process_data(self, data) -> None:

        if data is not None:

            fish_centroid = np.zeros((2,1), dtype=float)
            fish_caudorostral_axis = np.zeros((2,1), dtype=float)
            fish_mediolateral_axis = np.zeros((2,1), dtype=float)
            left_eye_centroid = np.zeros((2,1), dtype=float)
            right_eye_centroid = np.zeros((2,1), dtype=float)
            skeleton_interp = np.zeros((self.num_tail_points_interp,2), dtype=float)
            left_eye_angle = 0
            right_eye_angle = 0

            try:
                # TODO choose animal
                k = data['tracking']['animals']['identities'][0]

                if data['tracking']['body'][k] is not None:
                    fish_centroid[:] = data['tracking']['body'][k]['centroid_original_space']
                    heading = data['tracking']['body'][k]['heading']
                    fish_caudorostral_axis[:] = heading[:,0]
                    fish_mediolateral_axis[:] = heading[:,1]
                else:
                    fish_centroid[:] = data['tracking']['animals']['centroids'][k,:]

                # TODO use eyes heading vector if present?
                # eyes
                if data['tracking']['eyes'][k] is not None:

                    if data['tracking']['eyes'][k]['left_eye'] is not None:
                        left_eye_centroid[:] = data['tracking']['eyes'][k]['left_eye']['centroid'] 
                        left_eye_angle = data['tracking']['eyes'][k]['left_eye']['angle']

                    if data['tracking']['eyes'][k]['right_eye'] is not None:
                        right_eye_centroid[:] = data['tracking']['eyes'][k]['right_eye']['centroid']
                        right_eye_angle = data['tracking']['eyes'][k]['right_eye']['angle']

                # tail
                if data['tracking']['tail'][k] is not None:
                    skeleton_interp = data['tracking']['tail'][k]['skeleton_interp']  

                row = (
                    f'{data['index']}',
                    f'{data['timestamp']}',
                    f'{fish_centroid[0]}',
                    f'{fish_centroid[1]}',
                    f'{fish_caudorostral_axis[0]}',
                    f'{fish_caudorostral_axis[1]}',
                    f'{fish_mediolateral_axis[0]}',
                    f'{fish_mediolateral_axis[1]}',
                    f'{left_eye_centroid[0]}',
                    f'{left_eye_centroid[1]}',
                    f'{left_eye_angle}',
                    f'{right_eye_centroid[0]}',
                    f'{right_eye_centroid[1]}',
                    f'{right_eye_angle}',
                ) \
                + tuple(f'{skeleton_interp[i,0]}' for i in range(self.num_tail_points_interp)) \
                + tuple(f'{skeleton_interp[i,1]}' for i in range(self.num_tail_points_interp)) 
                self.fd.write(','.join(row) + '\n')

            except KeyError:
                return None 
            
            except TypeError:
                return None
            
            except ValueError:
                return None
            
    def process_metadata(self, metadata) -> None:
        pass