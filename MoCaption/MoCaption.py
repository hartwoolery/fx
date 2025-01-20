import numpy as np
import cv2
from fx_api.fx import FX, FrameInfo
from fx_api.utils.vector import Vector
class MoCaption(FX):
    def setup(self):
        self.requires_mask = True # if your fx requires segmentation of objects
        self.requires_inpainting = False # if your fx requires inpainting of objects

    def get_custom_inspector(self):
        return [
            {
                "always_showing": True,
                "type": "info",
                "label": "Info",
                "text": "Select a sprite and click 'Add Caption' to add a caption to the sprite that will follow above it."
            },
            {
                "show_for": "cutout",
                "label": "Caption",
                "type": "button",
                "text": "Add Caption",
                "action": self.add_caption
            }
        ]
    
    def add_caption(self):
        parent = self.current_sprite()
        caption = self.sprite_manager.add_sprite_of_type("text")
        caption.set_parent(parent)
        top_pos = parent.normalized_point_to_global(Vector(0,-1.2))
        caption.set_position(top_pos, frame_index=caption.start_keyframe.frame_index)
        

    def render_frame(self, frame_info: FrameInfo):
        super().render_frame(frame_info)