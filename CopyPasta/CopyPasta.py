import numpy as np
import cv2
from fx_api.fx import FX, FrameInfo
from fx_api.utils.vector import Vector

class CopyPasta(FX):
    def setup(self):
        self.requires_mask = True # if your fx requires segmentation of objects
        self.requires_inpainting = False # if your fx requires inpainting of objects

    def get_custom_inspector(self):
        return [
            {
                "always_showing": True,
                "type": "info",
                "label": "Info",
                "text": "Clone and scale below.  You can also clone and scale directly from the sprite's UI."
            },
            {
                "show_for": "all",
                "label": "Clone Sprite",
                "type": "button",
                "text": "Clone",
                "action": self.sprite_manager.clone_sprite,
            },
            {
                "show_for": "all",
                "type": "slider",
                "label": "Scale",
                "min": 1,
                "max": 200,
                "default": 100,
                "action": self.set_scale,
                "get_value": lambda: self.current_sprite().get_scale(local=True)[0] * 100
            }
        ]

    def set_scale(self, scale:float, finished=False):
        self.current_sprite().set_scale(Vector(scale/100, scale/100), local=True)

    def render_frame(self, frame_info: FrameInfo):
        super().render_frame(frame_info)
        