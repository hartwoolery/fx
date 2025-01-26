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
        uniform sampler2D u_blurredMask;
        uniform float u_glow_strength;
        uniform vec3 u_glow_color;

        void main() {
            vec2 uv = fragCoord.xy;
            float blurredVal = texture(u_blurredMask, uv).r;

            vec4 glowColor = vec4(u_glow_color/(1.1-blurredVal), 1.0);
            vec4 bloom = glowColor * blurredVal * u_glow_strength * 0.1;
            fragColor = bloom;
            fragColor.a = blurredVal;
        }
        """

        self.api.set_fragment_shader(glow_shader)


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
            {
                "show_for": "all",
                "type": "slider",
                "label": "Trail Length",
                "min": 1,
                "max": 100,
                "default": 50,
                "meta": "trail_length"
            }
        ]
    
    def clear_buffer(self, sprite):
        res = self.api.get_resolution()
        sprite.buffer = np.zeros((res[1], res[0], 3), dtype=np.uint8)

    def get_buffer(self, sprite):
        if not hasattr(sprite, "buffer"):
            self.clear_buffer(sprite)
        return sprite.buffer
        

    def combine_masks(self, mask1, mask2):
        # Step 1: Combine the masks
        combined_mask = cv2.bitwise_or(mask1[..., 0], mask2[..., 0])

        # Step 2: Find contours of the combined mask
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Step 3: Compute the convex hull of all contours
        if contours:
            all_points = np.vstack([point for contour in contours for point in contour])
            convex_hull = cv2.convexHull(all_points)
            # Step 4: Draw the convex hull on a new mask
            convex_mask = np.zeros_like(combined_mask)
            cv2.drawContours(convex_mask, [convex_hull], -1, 255, thickness=cv2.FILLED)
        else:
            convex_hull = np.array([])  # Handle empty contour case
            convex_mask = combined_mask

        
        
        # Apply Gaussian blur to the mask, not the contour
        smooth_contour = cv2.GaussianBlur(convex_mask, (5, 5), 0)
        
        gray = cv2.cvtColor(smooth_contour, cv2.COLOR_GRAY2BGR)

        return gray
    
    def render_frame(self, frame_info: FrameInfo):
        
        

        original_frame = frame_info.frame.copy()
        for sprite in self.sprite_manager.sprites:
            if sprite.mask is None:
                continue
            
            buffer = self.get_buffer(sprite)

            if frame_info.index == 0:
                self.clear_buffer(sprite)
            else:
                fade_factor = self.get_meta("trail_length", 50) / 100
                buffer = (buffer * fade_factor).astype(np.uint8)

            glow_strength = sprite.get_meta("glow_strength", 10)
            glow_color = sprite.get_meta("glow_color", (100, 255, 50))
            blur_radius = sprite.get_meta("blur_radius", 20)
            
            mask = sprite.get_mask_image()

            if frame_info.index > 0:
                prev_frame = frame_info.index - 1
                prev_mask = self.api.get_mask_image(prev_frame, sprite.object_info.id)
                if prev_mask is not None:
                    mask = self.combine_masks(mask, prev_mask)
            
            blurred_mask = cv2.GaussianBlur(mask, (0, 0), int(blur_radius/4)+1)
            

            ImageUtils.blend(buffer, blurred_mask, blend_mode="add")

            uniforms = {
                "u_blurredMask": buffer,
                "u_glow_strength": glow_strength, 
                "u_glow_color": glow_color
            }
            new_buffer = self.api.render_shader(uniforms)


            ImageUtils.blend(frame_info.render_buffer, new_buffer, blend_mode="normal")
                
        

        #frame_info.frame = original_frame
        for sprite in self.sprite_manager.sprites:
            sprite.render(frame_info)

        
        
    
        