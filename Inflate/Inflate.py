import numpy as np
import cv2
from fx_api.fx import FX, FrameInfo
from fx_api.utils.vector import Vector
from fx_api.utils.image import ImageUtils

class Inflate(FX):
    def setup(self):
        self.requires_mask = True # if your fx requires segmentation of objects
        self.requires_inpainting = True # if your fx requires inpainting of objects

        # a simple shader to convert the image to grayscale
        inflate_shader = r"""
#define SPEED 2.
#define RANGE .5
#define Strength .5

uniform sampler2D texSampler;
uniform sampler2D maskSampler;
uniform vec2 maskCenter;
uniform vec2 maskSize;
uniform float inflate_size;

vec2 inflate(vec2 uv, vec2 center, float radius, float strength) {
    float dist = distance(uv , center);
    vec2 dir = normalize(uv - center);
    float scale = 1.-strength + strength *smoothstep(0.,1.,dist/radius);
    float newDist = dist * scale;
    return center + newDist * dir;
}

void main()
{
    vec2 uv = fragCoord;
    
    vec2 pos = maskCenter / iResolution.xy;
    float radius = length(maskSize/iResolution.xy) * 0.5;
    uv = inflate(uv, pos, radius, inflate_size);
    vec3 color = texture(texSampler, uv).rgb;
    float alpha = texture(maskSampler, uv).r;
    fragColor.rgb = color;
    fragColor.a = alpha;
}
        """

        self.api.set_fragment_shader(inflate_shader)
   

    # called when the fx is ready
    def on_ready(self):
        super().on_ready() 

    def render_frame(self, frame_info: FrameInfo):
        #super().render_frame(frame_info)

        # to render the grayscale shader, uncomment the following code
        self.render_shader(frame_info)

    def render_shader(self, frame_info: FrameInfo):

        for sprite in self.sprite_manager.sprites:
            if sprite.mask is None:
                continue

            mask = sprite.get_mask_image()

            mask_bbox = sprite.bbox
            bbox_center = Vector((mask_bbox[0] + mask_bbox[2]) / 2, (mask_bbox[1] + mask_bbox[3]) / 2)
            bbox_size = Vector(mask_bbox[2] - mask_bbox[0], mask_bbox[3] - mask_bbox[1])

            inflate_size = sprite.get_meta("inflate_size", 0)/100
            if inflate_size > 0:
                new_tex = self.api.render_shader({
                    "texSampler": frame_info.frame,
                    "maskSampler": mask,
                    "maskCenter": bbox_center,
                    "maskSize": bbox_size,
                    "inflate_size": inflate_size,
                })
                # alpha blends the shader onto the frame
                #bgr_image = new_tex[:, :, :3]  # Extract BGR channels
                #alpha_image = new_tex[:, :, 3]  # Extract Alpha channel
                half_size = bbox_size/2
                expansion = (half_size * inflate_size * 1.0)
                x1, y1 = (bbox_center - half_size - expansion).round()
                x2, y2 = (bbox_center + half_size + expansion).round()
                #sprite.bbox = [x1, y1, x2, y2]
                # Crop the new texture using the sprite's bounding box
           
                height, width = new_tex.shape[:2]
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(width, x2)
                y2 = min(height, y2)
                new_tex_cropped = new_tex[y1:y2, x1:x2]
                new_size = (bbox_size * (inflate_size + 1)).round()
                half_new_size = new_size/2
                #sprite.bbox = [bbox_center.x - half_new_size.x, bbox_center.y - half_new_size.y, bbox_center.x + half_new_size.x, bbox_center.y + half_new_size.y]
                #sprite.update_bbox()
                new_tex_cropped = cv2.resize(new_tex_cropped, bbox_size, interpolation=cv2.INTER_LINEAR)
                

                
                sprite.blit_sprite(frame_info, new_tex_cropped, is_transformed=sprite.is_transformed())
                #ImageUtils.blend(frame_info.render_buffer, new_tex, position=Vector(0,0), centered=False, blend_mode="normal")
            else:
                sprite.render(frame_info)
    # below function customizes the inspector UI, see example_ui for the format
  
    
    def get_custom_inspector(self):
        return [
            # {
            #     "always_showing": True,
            #     "type": "info",
            #     "label": "Info",
            #     "text": "The playground is a sandbox for testing new features and ideas."
            # },
            # {
            #     "show_for": "all",
            #     "label": "Segmented",
            #     "type": "segmented_control",
            #     "default": 1,
            #     "segments": ["1", "2", "3"],
            #     "sprite_meta": "segmented"
            # },
            {
                "show_for": "cutout",
                "type": "slider",
                "label": "Inflate Size",
                "min": 0,
                "max": 100,
                "default": 0,
                "sprite_meta": "inflate_size"
            },
            # {
            #     "show_for": "all",
            #     "type": "number_input",
            #     "label": "Number",
            #     "min": 0,
            #     "max": 100,
            #     "default": 50,
            #     "sprite_meta": "number"
            # },
            # {
            #     "show_for": "all",
            #     "type": "font",
            #     "label": "Font",
            #     "text": "Choose A Font",
            #     "sprite_meta": "font"
            # },
            # {
            #     "show_for": "all",
            #     "type": "button",
            #     "label": "Button",
            #     "text": "Click Me",
            #     "sprite_meta": "button"
            # },
            # {
            #     "show_for": "all",
            #     "type": "text_input",
            #     "label": "Text",
            #     "text": "Enter Text",
            #     "sprite_meta": "text"
            # },
            # {
            #     "show_for": "all",
            #     "type": "checkbox",
            #     "label": "Checkbox",
            #     "default": True,
            #     "sprite_meta": "checkbox"
            # },
            # {
            #     "show_for": "all",
            #     "type": "dropdown",
            #     "label": "Dropdown",
            #     "default": "Option 1",
            #     "options": ["Option 1", "Option 2", "Option 3"],
            #     "sprite_meta": "dropdown"
            # }
        ]
    
        