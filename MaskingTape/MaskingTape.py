import numpy as np
import cv2
from fx_api.fx import FX, FrameInfo

class MaskingTape(FX):
    def setup(self):
        self.requires_mask = True # if your fx requires segmentation of objects
        self.requires_inpainting = False # if your fx requires inpainting of objects
        self.requires_sprites = True # if your fx requires sprites to manipulate objects
        

    def get_custom_inspector(self):
        return [
            {
                "always_showing": True,
                "type": "info",
                "label": "Info",
                "text": "Mask or invert mask anything in the scene by picking colors. Select a sprite to inverse mask the foreground."
            },
            {
                "always_showing": True,
                "label": "BG Color",
                "type": "color_picker",
                "default": None,
                "meta": "background_color"
            },
            {
                "show_for": "cutout",
                "label": "FG Color",
                "type": "color_picker",
                "default": None,
                "sprite_meta": "foreground_color"
            }
        ]


    
    def render_frame(self, frame_info: FrameInfo):
        #super().render_frame(frame_info)

        bg_color = self.get_meta("background_color", None)
        if bg_color:
            frame_info.render_buffer[:] = np.array(bg_color)
        
        original_frame = frame_info.frame.copy()
        for sprite in self.sprite_manager.sprites:
            if sprite.type == "cutout":
                color = sprite.get_meta("foreground_color", None)
                
                if color is not None:
                    frame_info.frame = original_frame.copy()
                    frame_info.frame[:] = color  # Fill the entire frame with the foreground color
       
              
            
            sprite.render(frame_info)
            frame_info.frame = original_frame.copy()

    