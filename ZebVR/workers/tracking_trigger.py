import numpy as np 
from numpy.typing import NDArray
from dagline import WorkerNode
from collections import defaultdict
from ZebVR.widgets import Stim

class TrackingTrigger(WorkerNode):

    def __init__(
            self, 
            trigger_mask: NDArray,
            *args, 
            **kwargs
        ) -> None:

        '''
        trigger_mask is a 2D boolean array that contains 1 at position (x,y) if there should be 
        a trigger.
        '''

        super().__init__(*args, **kwargs)
        self.trigger_mask = trigger_mask
        self.triggered = False

    def initialize(self):
        super().initialize()
        
    def cleanup(self):
        super().cleanup()

    def process_data(self, data) -> None:

        if data is not None:

            fish_centroid = np.zeros((2,), dtype=float)

            try:
                # TODO choose animal
                k = data['tracking']['animals']['identities'][0]

                if data['tracking']['body'][k] is not None:
                    fish_centroid[:] = data['tracking']['body'][k]['centroid_original_space']
                else:
                    fish_centroid[:] = data['tracking']['animals']['centroids'][k,:]

            except KeyError:
                return 
            
            except TypeError:
                return
            
            except ValueError:
                return

            x, y = fish_centroid.astype(int)
            if self.trigger_mask[y, x] == 1:
                self.triggered = True
                
    def process_metadata(self, metadata) -> None:

        # TODO relay a trigger to the protocol worker instead of hardcoding
        
        if self.triggered:

            command = defaultdict(float, {
                'stim_select': Stim.BRIGHT,
                'foreground_color': (1.0,0.0,0.0,1.0),
                'background_color': (0.0,0.0,0.0,1.0),
                'looming_center_mm': (0, 0)
            })
            
            res = {}
            res['visual_stim_control'] = command

            # TODO maybe add filtering to avoid flicker
            self.triggered = False
            
            return res
