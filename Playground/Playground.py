import numpy as np
import cv2
from fx_api.fx import FX, FrameInfo
from fx_api.utils.vector import Vector
from fx_api.utils.image import ImageUtils

class Playground(FX):
    def setup(self):
        self.requires_mask = True # if your fx requires segmentation of objects
        self.requires_inpainting = True # if your fx requires inpainting of objects

        # a simple shader to convert the image to grayscale
        grayscale_shader = r"""

        uniform sampler2D texSampler;

        void main()
        {
            vec4 color = texture(texSampler, fragCoord);
            float gray = dot(color.rgb, vec3(0.299, 0.587, 0.114));
            fragColor = vec4(vec3(gray), color.a);
        }
        """

        self.api.set_fragment_shader(grayscale_shader)
   

    # called when the fx is ready
    def on_ready(self):
        super().on_ready() 

    def render_frame(self, frame_info: FrameInfo):
        super().render_frame(frame_info)

        # to render the grayscale shader, uncomment the following code
        # self.render_shader(frame_info)

    def render_shader(self, frame_info: FrameInfo):
        new_tex = self.api.render_shader({
            "texSampler": frame_info.frame
        })
        # alpha blends the shader onto the frame
        ImageUtils.blend(frame_info.render_buffer, new_tex, position=Vector(0,0), centered=False, blend_mode="normal")
    
    # below function customizes the inspector UI, see example_ui for the format
      
    example_ui = r"""
    { 
        "always_showing": bool, # if true, the UI element will always be shown regardless of whether a sprite is selected
        "show_for": str, # comma-separated list of the types of sprites this UI element will be shown for eg "all", "cutout", "image", "video", "text"
        "type": str, # the type of UI element to show eg "info", "button", "slider", "segmented_control", "color_picker", "text_input", "checkbox", "dropdown", "font"
        "label": str, # the label to the left of the UI element
        "text": str, # the text of the UI element
        "alpha": bool, # for color pickers, if True, the UI element will have an alpha channel
        "default": any, # the default value of the UI element
        "options": list[str], # for dropdowns, the list of options to show
        "min": int, # the minimum value of the UI element if supported
        "max": int, # the maximum value of the UI element if supported
        "suffix": str, # for sliders, the suffix of the slider label eg "%", "px", "deg", etc
        "action": function(val:any, finished:bool), # the function to call when the UI element is changed, for sliders and color pickers a finished boolean is passed as the second argument
        "get_value": function()->any, # the function to retrieve the value of the UI element
        "sprite_meta": str, # a special key to store the value of the UI element to the selected sprite's meta data, which is also keyframed on change.  It handles changes to rendering automatically
        "meta": str # a special key to store a general value that applies to everything rather than individual sprites
    }
    """
    
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
            # {
            #     "show_for": "all",
            #     "type": "slider",
            #     "label": "Slider",
            #     "min": 0,
            #     "max": 100,
            #     "default": 50,
            #     "sprite_meta": "slider"
            # },
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
    
        