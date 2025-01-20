import numpy as np
import cv2
from fx_api.fx import FX, FrameInfo

class Eraser(FX):
    def setup(self):
        self.requires_mask = True # if your fx requires segmentation of objects
        self.requires_inpainting = True # if your fx requires inpainting of objects

    def render_frame(self, frame_info: FrameInfo):
        frame = self.api.get_inpainting(frame_info)
        return frame 
    
    
    # override and do not add default sprites
    def on_ready(self):
        self.is_ready = True