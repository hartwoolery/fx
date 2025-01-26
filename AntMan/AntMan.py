import numpy as np
import cv2
from fx_api.fx import FX, FrameInfo
from fx_api.utils.vector import Vector
from fx_api.utils.image import ImageUtils

class AntMan(FX):
    def setup(self):
        self.requires_mask = True # if your fx requires segmentation of objects
        self.requires_inpainting = True # if your fx requires inpainting of objects
        self.requires_pose = False # if your fx requires pose estimation

        self.tiny_size = Vector(30, 30)
        self.normal_size = Vector(100, 100)
        self.giant_size = Vector(200, 200)

    def on_ready(self):
        super().on_ready()
        #move the anchor point to the bottom of the sprite to simulate shrinking/growing from the ground
        for spr in self.sprite_manager.sprites:
            spr.set_anchor_point_normalized(Vector(0.0, 0.9))

    def render_frame(self, frame_info: FrameInfo):
        super().render_frame(frame_info)
        # new_tex = self.api.render_shader({
        #     "texSampler": frame_info.frame
        # })
        # ImageUtils.blend(frame_info.render_buffer, new_tex)
    
    def get_custom_inspector(self):
        return [
            {
                "always_showing": True,
                "type": "info",
                "label": "Info",
                "text": "Choose a frame and object in the video and click Tiny/Giant and see the object shrink/grow. Play with Easing to change the speed of the animation."
            },
            {
                "show_for": "all",
                "label": "Size",
                "type": "segmented_control",
                "default": 1,
                "segments": ["Tiny", "Normal", "Giant"],
                "action": self.set_size,
                "get_value": lambda: 1
            },
            {
                "show_for": "all",
                "type": "slider",
                "label": "Tiny Scale",
                "min": 1,
                "max": 99,
                "default": 50,
                "action": self.set_tiny_scale,
                "get_value": lambda: self.tiny_size.x 
            },
            {
                "show_for": "all",
                "type": "slider",
                "label": "Giant Scale",
                "min": 101,
                "max": 400,
                "default": 200,
                "action": self.set_giant_scale,
                "get_value": lambda: self.giant_size.x 
            }
        ]
    
    def set_tiny_scale(self, value, finished):
        self.tiny_size = Vector(value, value)
        self.update_existing_keyframes()

    
    def set_giant_scale(self, value, finished):
        self.giant_size = Vector(value, value)
        self.update_existing_keyframes()

    def update_existing_keyframes(self):
        for spr in self.sprite_manager.sprites:
            for keyframe in spr.keyframes:
                scale_x, scale_y = keyframe.transform.get("scale", Vector(1.0, 1.0))
                if scale_x < 1.0:
                    spr.set_scale(self.tiny_size * 0.01, frame_index=keyframe.frame_index)
                elif scale_x > 1.0:
                    spr.set_scale(self.giant_size * 0.01, frame_index=keyframe.frame_index)
    
    def set_size(self, index, segment):
        if segment == "Tiny":
            self.sprite_manager.selected_sprite.set_scale(self.tiny_size * 0.01)       
        elif segment == "Normal":
            self.sprite_manager.selected_sprite.set_scale(self.normal_size * 0.01)
        elif segment == "Giant":
            self.sprite_manager.selected_sprite.set_scale(self.giant_size * 0.01)
        