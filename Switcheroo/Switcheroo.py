import numpy as np
import cv2
from fx_api.fx import FX, FrameInfo

class Switcheroo(FX):
    def setup(self):
        self.requires_mask = True # if your fx requires segmentation of objects
        self.requires_inpainting = True # if your fx requires inpainting of objects

    def get_custom_inspector(self):
        return [
            {
                "always_showing": True,
                "type": "info",
                "label": "Info",
                "text": "Select a sprite to replace and click 'Replace With Image/Video' to load a replacement."
            },
            {
                "show_for": "cutout",
                "label": "Image",
                "type": "button",
                "text": "Replace With Image",
                "action": lambda: self.replace_with("image")
            },
            {
                "show_for": "cutout",
                "label": "Video",
                "type": "button",
                "text": "Replace With Video",
                "action": lambda: self.replace_with("video")
            }
        ]

    def replace_with(self, type:str):
        sprite = self.current_sprite()
        parent = sprite.parent

        new_sprite = self.sprite_manager.add_sprite_of_type(type, parent=parent)
        if new_sprite is None:
            return
        
        self.sprite_manager.delete_sprite(sprite)



    def render_frame(self, frame_info: FrameInfo):
        super().render_frame(frame_info)