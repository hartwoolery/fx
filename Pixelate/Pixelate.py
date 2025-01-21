import numpy as np
import cv2
from fx_api.fx import FX, FrameInfo

class Pixelate(FX):
    def setup(self):
        self.requires_mask = True # if your fx requires segmentation of objects
        self.requires_inpainting = False # if your fx requires inpainting of objects

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
                "label": "Pixel Size",
                "type": "slider",
                "min": 1,
                "max": 30,
                "action": self.set_pixel_size,
                "get_value": lambda: self.current_sprite().get_meta("pixel_size", 1)
            },
            {
                "show_for": "all",
                "label": "Pixel Color",
                "type": "color_picker",
                "default": None,
                "action": self.change_pixel_color,
                "get_value": lambda: self.current_sprite().get_meta("pixel_color", None)
            }
        ]
    
    def set_pixel_size(self, value, finished:bool=False):
        self.current_sprite().set_meta("pixel_size", value)
        self.refresh_frame()

    def change_pixel_color(self, color):
        self.current_sprite().set_meta("pixel_color", color)
        self.refresh_frame()


    def render_frame(self, frame_info: FrameInfo):
        #super().render_frame(frame_info)

        pixel_size = self.current_sprite().get_meta("pixel_size", 1)
        pixel_color = self.current_sprite().get_meta("pixel_color", None)


        for sprite in self.sprite_manager.sprites:
            if pixel_size > 1:
                bbox = sprite.bbox
                if (bbox[2] - bbox[0] == 0) or (bbox[3] - bbox[1] == 0):
                    continue
                # Expand the bounding box by a small margin
                margin = 5  # Adjust this value as needed
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
                
                if sprite.mask is not None:
                    mask_crop = sprite.mask.copy().astype(np.uint8)[expanded_bbox[1]:expanded_bbox[3], expanded_bbox[0]:expanded_bbox[2]]
                    # Pixelate the mask
                    kernel = np.ones((3, 3), np.uint8)  # Create a 3x3 kernel for dilation
                    mask_crop = cv2.dilate(mask_crop, kernel, iterations=1)  # Dilate the mask crop

                    mask_crop = cv2.resize(mask_crop, (0, 0), fx=1/pixel_size, fy=1/pixel_size, interpolation=cv2.INTER_NEAREST)
                    mask_crop = cv2.resize(mask_crop, (width,height), interpolation=cv2.INTER_NEAREST)
                    sprite.mask[expanded_bbox[1]:expanded_bbox[3], expanded_bbox[0]:expanded_bbox[2]] = mask_crop

                frame_crop = frame_info.frame[expanded_bbox[1]:expanded_bbox[3], expanded_bbox[0]:expanded_bbox[2]]
                
                # Pixelate the frame
                frame_crop = cv2.resize(frame_crop, (0, 0), fx=1/pixel_size, fy=1/pixel_size, interpolation=cv2.INTER_NEAREST)
                if pixel_color is not None:
                    hsv_color = cv2.cvtColor(np.uint8([[pixel_color]]), cv2.COLOR_BGR2HSV)[0][0]  # Convert pixel color to HSV
                    # Create a random noise array for the V channel
                    noise = np.random.randint(-20, 20, size=frame_crop.shape[:2], dtype=np.int16)  # Generate random noise for V channel
                    hsv_frame = np.full_like(frame_crop, hsv_color, dtype=np.uint8)  # Create an HSV frame with the base color
                    hsv_frame[..., 2] = np.clip(hsv_frame[..., 2] + noise, 0, 255)  # Modify V channel with noise
                    frame_crop = cv2.cvtColor(hsv_frame, cv2.COLOR_HSV2BGR)  # Convert back to BGR
                frame_crop = cv2.resize(frame_crop, (width, height), interpolation=cv2.INTER_NEAREST)

                

                # Update the sprite's frame with the pixelated version
                frame_info.frame[expanded_bbox[1]:expanded_bbox[3], expanded_bbox[0]:expanded_bbox[2]] = frame_crop
            sprite.render(frame_info)
                

