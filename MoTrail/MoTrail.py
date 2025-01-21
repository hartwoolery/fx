import numpy as np
import cv2
from fx_api.fx import FX, FrameInfo
from fx_api.utils.image import ImageUtils
from fx_api.utils.vector import Vector
class MoTrail(FX):
    def setup(self):
        self.requires_mask = True  # if your fx requires segmentation of objects
        self.requires_inpainting = False  # if your fx requires inpainting of objects
        self.trail_length = 50
        self.buffer = np.zeros((*self.api.get_resolution(), 4), dtype=np.uint8)  # Create an empty nparray with alpha channel

    def get_custom_inspector(self):
        return [
            {
                "always_showing": True,
                "type": "info",
                "label": "Info",
                "text": "Sprites are automatically motion trailed.  Uncheck to disable."
            },
            {
                "show_for": "all",
                "label": "Trail",
                "type": "checkbox",
                "default": True,
                "text": "Enable Motion Trail",
                "action": self.set_enable_trail,
                "get_value": lambda: self.current_sprite().get_meta("enable_trail", True)
            },
            {
                "show_for": "all",
                "label": "Trail Length",
                "type": "slider",
                "min": 1,
                "max": 99,
                "default": self.trail_length,
                "action": self.set_trail_length,
                "get_value": lambda: self.trail_length
            }

        ]
    

    def set_enable_trail(self, value, finished:bool=False):
        self.current_sprite().set_meta("enable_trail", value)
        self.refresh_frame()
    
    def set_trail_length(self, value, finished:bool=False):
        self.trail_length = value
        self.refresh_frame()
    def clear_buffer(self):
        self.buffer = np.zeros((*self.api.get_resolution(), 4), dtype=np.uint8)

    def render_frame(self, frame_info: FrameInfo):
        #super().render_frame(frame_info)

        if frame_info.index == 0:
            self.clear_buffer()
        else:
            self.buffer[..., 3] = (self.buffer[..., 3] * (0.6 + self.trail_length / 250)).astype(np.uint8)


        original_frame = frame_info.frame.copy()
        

        for sprite in self.sprite_manager.sprites:
            enable_trail = sprite.get_meta("enable_trail", True)
            frame_info.override_buffer = self.buffer if enable_trail else None
            color = (255, 0, 255)
            frame_info.frame[:] = color 
            sprite.render(frame_info)
            
            

        ImageUtils.blend(frame_info.render_buffer, self.buffer, Vector(0,0), centered=False, blend_mode="normal")

        frame_info.frame = original_frame
        for sprite in self.sprite_manager.sprites:
            frame_info.override_buffer = None
            sprite.render(frame_info)



                


