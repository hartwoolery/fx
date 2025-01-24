import numpy as np
import cv2
from fx_api.fx import FX, FrameInfo
from fx_api.utils.vector import Vector
from fx_api.utils.image import ImageUtils

class Edgy(FX):
    def setup(self):
        self.requires_mask = True # if your fx requires segmentation of objects
        self.requires_inpainting = True # if your fx requires inpainting of objects

        glow_shader = r"""
        uniform sampler2D u_texture;
        uniform sampler2D u_mask;
        uniform sampler2D u_blurredMask;
        uniform float u_glow_strength;
        uniform vec3 u_glow_color;

        void main() {
            vec4 baseColor = texture(u_texture, fragCoord);
            float maskVal = texture(u_mask, fragCoord).r;
            float blurredVal = texture(u_blurredMask, fragCoord).r;

            baseColor.a = blurredVal;
            vec4 glowColor = vec4(u_glow_color/(1.1-blurredVal), 1.0);
            vec4 bloom = glowColor * blurredVal * u_glow_strength;
            fragColor = baseColor + bloom;
            if (maskVal == 1.0) {
                fragColor.a = 0.0;// baseColor;
            }
            
            // (Optional) If you want the object itself to remain un-bloomed in the center,
            // or do some custom mix inside vs outside the mask, you can do further logic here.
            
        }
        """

        self.api.set_fragment_shader(glow_shader)

        res = self.api.get_resolution()
        self.buffer = np.zeros((res[1], res[0], 4), dtype=np.uint8)  # Create an empty nparray with alpha channel

    def on_ready(self):
        super().on_ready()
        #move the anchor point to the bottom of the sprite to simulate shrinking/growing from the ground
        for spr in self.sprite_manager.sprites:
            spr.set_anchor_point_normalized(Vector(0.0, 0.9))

    def get_custom_inspector(self):
        return [
            {
                "always_showing": True,
                "type": "info",
                "label": "Info",
                "text": "Choose a frame and object in the video and click setup the glow size and color"
            },
            {
                "show_for": "all",
                "type": "color_picker",
                "label": "Glow Color",
                "default": (100, 255, 50),
                "sprite_meta": "glow_color",
            },
            {
                "show_for": "all",
                "type": "slider",
                "label": "Glow Strength",
                "min": 0,
                "max": 100,
                "default": 10,
                "sprite_meta": "glow_strength"
            },
            {
                "show_for": "all",
                "type": "slider",
                "label": "Blur Radius",
                "min": 1,
                "max": 100,
                "default": 20,
                "sprite_meta": "blur_radius"
            },
       
        ]
    

    def clear_buffer(self):
        res = self.api.get_resolution()
        self.buffer = np.zeros((res[1], res[0], 4), dtype=np.uint8)
        
    

    def render_frame(self, frame_info: FrameInfo):
        
        if frame_info.index == 0:
            self.clear_buffer()
        else:
            fade_factor = 0.6 + self.get_meta("trail_length", 50) / 250
            self.buffer[..., 3] = (self.buffer[..., 3] * fade_factor).astype(np.uint8)

        original_frame = frame_info.frame.copy()
        print(frame_info.frame.shape, "frame_info.frame.shape")
        for sprite in self.sprite_manager.sprites:
            if sprite.mask is None:
                continue

            glow_strength = sprite.get_meta("glow_strength", 10)
            glow_color = sprite.get_meta("glow_color", (100, 255, 50))
            blur_radius = sprite.get_meta("blur_radius", 20)
            mask = sprite.get_mask_image()
            blurred_mask = cv2.GaussianBlur(mask, (0, 0), int(blur_radius/4)+1)
            
            #enable_trail = sprite.get_meta("enable_trail", True)
            #frame_info.override_buffer = self.buffer if enable_trail else None
            #trail_color = sprite.get_meta("trail_color", None)
        
            # if trail_color is not None:
            #     frame_info.frame[:] = trail_color 
            # else:
            #     frame_info.frame = original_frame
            
            # original_blend = sprite.blend_mode
            # sprite.blend_mode = sprite.get_meta("trail_blend", "Normal")
            # sprite.render(frame_info)
            # sprite.blend_mode = original_blend
            uniforms = {
                "u_texture": frame_info.frame,
                "u_mask": mask,
                "u_blurredMask": blurred_mask,
                "u_glow_strength": glow_strength, 
                "u_glow_color": glow_color
            }
            new_buffer = self.api.render_shader(uniforms)


            if new_buffer is not None:
                ImageUtils.blend(self.buffer, new_buffer)
                
                #ImageUtils.blend(frame_info.render_buffer, new_buffer)
        

        ImageUtils.blend(frame_info.render_buffer, self.buffer)

        frame_info.frame = original_frame
        for sprite in self.sprite_manager.sprites:
            frame_info.override_buffer = None
            sprite.render(frame_info)

        
        
    
        