import numpy as np
import cv2
from fx_api.fx import FX, FrameInfo

class Pixelate(FX):
    def setup(self):
        self.requires_mask = True # if your fx requires segmentation of objects
        self.requires_inpainting = True # if your fx requires inpainting of objects

    def get_custom_inspector(self):
        return [
            {
                "always_showing": True,
                "type": "info",
                "label": "Info",
                "text": "Select a sprite to pixelate and modify the color and size of the pixelation."
            },
            {
                "show_for": "all",
                "label": "Inpaint",
                "type": "checkbox",
                "default": True,
                "text": "Use Inpainting",
                "sprite_meta": "use_inpaint"
            },
            {
                "show_for": "all",
                "label": "Pixel Size",
                "type": "slider",
                "min": 1,
                "max": 30,
                "default": 15,
                "sprite_meta": "pixel_size"
            },
            {
                "show_for": "all",
                "label": "Expand Mask",
                "type": "slider",
                "min": 0,
                "max": 100,
                "default": 10,
                "sprite_meta": "expansion"
            },
            {
                "show_for": "all",
                "label": "Pixel Color",
                "type": "color_picker",
                "default": None,
                "sprite_meta": "pixel_color"
            }
        ]

        
    # override to not show inpainting by default
    def render_background(self, frame_info: FrameInfo):
        pixelate = False
        for sprite in self.sprite_manager.sprites:
            pixel_size = sprite.get_meta("pixel_size", 1)
            use_inpaint = sprite.get_meta("use_inpaint", True)
            if pixel_size > 1 and use_inpaint:
                pixelate = True
        
        if pixelate:
            frame_info.render_buffer = self.api.get_inpainting(frame_info)
        else:
            frame_info.render_buffer = frame_info.frame.copy()


    def render_frame(self, frame_info: FrameInfo):
        #super().render_frame(frame_info)



        for sprite in self.sprite_manager.sprites:

            pixel_size = sprite.get_meta("pixel_size", 1)
            pixel_color = sprite.get_meta("pixel_color", None)
            if pixel_size > 1:
                bbox = sprite.bbox
                expansion = sprite.get_meta("expansion", 10)
                original_width = bbox[2] - bbox[0]
                original_height = bbox[3] - bbox[1]
                if original_width == 0 or original_height == 0:
                    continue
                # Expand the bounding box by a small margin
                margin = int(expansion * original_width / 100)   # Adjust this value as needed
             
                expanded_bbox = (
                    max(bbox[0] - margin, 0),  # x1, clipped to 0
                    max(bbox[1] - margin, 0),  # y1, clipped to 0
                    min(bbox[2] + margin, frame_info.frame.shape[1]),  # x2, clipped to frame width
                    min(bbox[3] + margin, frame_info.frame.shape[0])   # y2, clipped to frame height
                )
                
                # Update the sprite's bounding box
                sprite.bbox = expanded_bbox
                width = expanded_bbox[2] - expanded_bbox[0]
                height = expanded_bbox[3] - expanded_bbox[1]
                use_inpaint = sprite.get_meta("use_inpaint", True)
                if use_inpaint:
                    frame_crop = self.api.get_inpainting(frame_info)
                else:
                    frame_crop = frame_info.frame.copy()
                
                frame_crop = frame_crop[expanded_bbox[1]:expanded_bbox[3], expanded_bbox[0]:expanded_bbox[2]]
                mask_crop = np.ones((height, width), dtype=np.uint8)
                if sprite.mask is not None:
                    mask_crop = sprite.mask.copy().astype(np.uint8)[expanded_bbox[1]:expanded_bbox[3], expanded_bbox[0]:expanded_bbox[2]]
                   
                    mask_crop = cv2.dilate(mask_crop, cv2.getStructuringElement(cv2.MORPH_CROSS, (5, 5)), iterations=int(expansion / 2))
            
                    mask_crop = cv2.resize(mask_crop, (0, 0), fx=1/pixel_size, fy=1/pixel_size, interpolation=cv2.INTER_NEAREST)
                    mask_crop = cv2.resize(mask_crop, (width,height), interpolation=cv2.INTER_NEAREST)
                    sprite.mask[expanded_bbox[1]:expanded_bbox[3], expanded_bbox[0]:expanded_bbox[2]] = mask_crop

                if pixel_color is not None:
                    # Convert the frame_crop to HSV color space
                    hsv_frame_crop = cv2.cvtColor(frame_crop, cv2.COLOR_BGR2HSV)
                    
                    # Calculate the average V value in the masked area
                    # masked_v_values = hsv_frame_crop[mask_crop > 0, 2]
                    # average_v = np.mean(masked_v_values) if masked_v_values.size > 0 else 0

                    # Create a new color in HSV with the same H and S as pixel_color, but with the average V
                    pixel_color_hsv = cv2.cvtColor(np.uint8([[pixel_color]]), cv2.COLOR_BGR2HSV)[0][0]
                    
                    
                    # Convert back to BGR color space
                    new_pixel_color = cv2.cvtColor(np.uint8([[pixel_color_hsv]]), cv2.COLOR_HSV2BGR)[0][0]
                    # Calculate the new V value for the recolored pixels
                    new_pixel_color_v = pixel_color_hsv[2]
                    # recolored_v = hsv_frame_crop[..., 2] - average_v + new_pixel_color_v
                    # recolored_v = np.clip(recolored_v, 0, 255)  # Ensure V values are within valid range
                    noise = np.random.normal(-10, 10, hsv_frame_crop[..., 2].shape)  # Generate noise
                    recolored_v = new_pixel_color_v + noise  # Add noise to the new V value
                    recolored_v = np.clip(recolored_v, 0, 255)  # Ensure V values are within valid range

                    # Create a new HSV image with the modified V channel
                    recolored_hsv_frame_crop = hsv_frame_crop.copy()
                    recolored_hsv_frame_crop[..., 2] = recolored_v
                    recolored_hsv_frame_crop[..., 1] = pixel_color_hsv[1]
                    recolored_hsv_frame_crop[..., 0] = pixel_color_hsv[0]

                    # Convert back to BGR color space
                    recolored_frame_crop = cv2.cvtColor(recolored_hsv_frame_crop, cv2.COLOR_HSV2BGR)
                    
                    # Change the color of the pixels inside the masked area
                    mask_indices = np.where(mask_crop > 0)
                    frame_crop[mask_indices] = recolored_frame_crop[mask_indices]
                
                    

                   

                    
                
                # Pixelate the frame
                frame_crop = cv2.resize(frame_crop, (0, 0), fx=1/pixel_size, fy=1/pixel_size, interpolation=cv2.INTER_NEAREST)
                
                frame_crop = cv2.resize(frame_crop, (width, height), interpolation=cv2.INTER_NEAREST)

                

                # Update the sprite's frame with the pixelated version
                frame_info.frame[expanded_bbox[1]:expanded_bbox[3], expanded_bbox[0]:expanded_bbox[2]] = frame_crop
            sprite.render(frame_info)
                

