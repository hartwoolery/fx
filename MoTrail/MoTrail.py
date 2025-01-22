import numpy as np
import cv2
from fx_api.fx import FX, FrameInfo
from fx_api.utils.image import ImageUtils
from fx_api.utils.vector import Vector
class MoTrail(FX):
    def setup(self):
        self.requires_mask = True  # if your fx requires segmentation of objects
        self.requires_inpainting = False  # if your fx requires inpainting of objects
        
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
                "sprite_meta": "enable_trail"
            },
            {
                "show_for": "all",
                "label": "Trail Length",
                "type": "slider",
                "min": 1,
                "max": 99,
                "default": 50,
                "meta": "trail_length"
            },
            {
                "show_for": "all",
                "label": "Trail Color",
                "type": "color_picker",
                "default": None,
                "sprite_meta": "trail_color"
            },
            {
                "show_for": "all",
                "type": "dropdown",
                "label": "Trail Blend",
                "options": ["Normal", "Additive", "Subtractive", "Multiply", "Screen", "Overlay", "Darken", "Lighten", "Color Dodge", "Color Burn", "Hard Light", "Soft Light", "Difference", "Exclusion", "Hue", "Saturation", "Color", "Luminosity"],
                "default": "Normal",
                "sprite_meta": "trail_blend"
            }
            

        ]
    

    def clear_buffer(self):
        self.buffer = np.zeros((*self.api.get_resolution(), 4), dtype=np.uint8)

    def render_frame(self, frame_info: FrameInfo):
        #super().render_frame(frame_info)

        if frame_info.index == 0:
            self.clear_buffer()
        else:
            fade_factor = 0.6 + self.get_meta("trail_length", 50) / 250
            self.buffer[..., 3] = (self.buffer[..., 3] * fade_factor).astype(np.uint8)


        original_frame = frame_info.frame.copy()
        

        for sprite in self.sprite_manager.sprites:
            enable_trail = sprite.get_meta("enable_trail", True)
            frame_info.override_buffer = self.buffer if enable_trail else None
            trail_color = sprite.get_meta("trail_color", None)
        
            if trail_color is not None:
                frame_info.frame[:] = trail_color 
            else:
                frame_info.frame = original_frame
            
            original_blend = sprite.blend_mode
            sprite.blend_mode = sprite.get_meta("trail_blend", "Normal")
            sprite.render(frame_info)
            sprite.blend_mode = original_blend
            

        ImageUtils.blend(frame_info.render_buffer, self.buffer, Vector(0,0), centered=False, blend_mode="normal")

        frame_info.frame = original_frame
        for sprite in self.sprite_manager.sprites:
            frame_info.override_buffer = None
            sprite.render(frame_info)



                


