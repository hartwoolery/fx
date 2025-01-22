import numpy as np
import cv2
from fx_api.fx import FX, FrameInfo
from fx_api.utils.anchor_manager import AnchorManager, ANCHOR_ID
from fx_api.utils.vector import Vector
from fx_api.utils.image import ImageUtils


from math import comb  # Available in Python 3.8+

class GoGoGadget(FX):
    def setup(self):
        self.requires_pose = True
        self.requires_mask = True # if your fx requires segmentation of objects
        self.requires_inpainting = True # if your fx requires inpainting of objects
        self.requires_sprites = True # if your fx requires sprites to manipulate objects
        self.default_link_size = 50

    def on_ready(self):
        super().on_ready()

        self.link_original = self.get_image_resource("link.png") 

    def bezier_curve_fit(self,image, points, num_points=100, color=(0, 255, 0), thickness=2):
        """
        Fits a Bézier curve to a set of points and draws it on a given OpenCV image.
        
        Args:
            image (np.ndarray): OpenCV image where the curve will be drawn.
            points (list of tuple): List of points (x, y) to fit the Bézier curve.
            num_points (int): Number of points to sample along the Bézier curve.
            color (tuple): Color of the curve (B, G, R).
            thickness (int): Thickness of the curve.
        
        Returns:
            np.ndarray: Image with the Bézier curve drawn.
        """
        def bernstein_poly(i, n, t):
            """Compute the Bernstein polynomial."""
            return comb(n, i) * (t**i) * ((1 - t)**(n - i))

        def bezier_curve(control_points, num_points):
            """Generate a Bézier curve from control points."""
            n = len(control_points) - 1  # Degree of the Bézier curve
            t_values = np.linspace(0, 1, num_points)
            curve = np.zeros((num_points, 2))
            for i in range(n + 1):
                curve += np.outer(bernstein_poly(i, n, t_values), control_points[i])
            return curve.astype(int)

        # Ensure points are a NumPy array
        points = np.array(points)
        
        # Generate Bézier curve
        bezier_points = bezier_curve(points, num_points)

        # Draw the Bézier curve on the image
        for i in range(1, len(bezier_points)):
            p1 = tuple(bezier_points[i - 1])
            p2 = tuple(bezier_points[i])
            #cv2.line(image, p1, p2, color, thickness)

            link = self.link_img.copy()
            # Calculate angle between p1 and p2
            angle = -(np.degrees(np.arctan2(p2[1] - p1[1], p2[0] - p1[0])) - 90)
            
            # Create rotation matrix
            M = cv2.getRotationMatrix2D((link.shape[1]//2, link.shape[0]//2), angle, 1.0)
            
            # Rotate the link image
            rotated_link = cv2.warpAffine(link, M, (link.shape[1], link.shape[0]))
            
            # Draw the rotated link at p1
            x = p1[0] - rotated_link.shape[1]//2
            y = p1[1] - rotated_link.shape[0]//2
            

            ImageUtils.blend(image, rotated_link, Vector(x,y))
        
        
        return image

    def render_links(self, frame_info: FrameInfo, sprite):
        # Get current transform for this sprite
        transform = sprite.local_transform.copy()
        # print(transform)
        # if 'translation' in transform:


        anchor = sprite.local_to_global(sprite.anchor_point)
        parent_anchor = sprite.parent.local_to_global(sprite.anchor_point)
        tx = anchor[0] - parent_anchor[0]
        ty = anchor[1] - parent_anchor[1]

        # Calculate angle between original and translated position
        angle = np.degrees(np.arctan2(ty, tx))

        # Calculate distance between original and translated position
        distance = np.sqrt(tx*tx + ty*ty)
        
        # Calculate number of circles to draw (1 circle per 5 pixels)
        num_circles = int(distance // 1) + 1
        scale = sprite.get_meta("link_size", self.default_link_size)
        def get_point(ratio, wa, y_offset=0):
            x = int(tx * ratio) + wa[0]
            y = int(ty * ratio) + wa[1] + y_offset
            return x,y

        thickness = 4


        self.link_img = self.link_original.copy()
        lh,lw = self.link_img.shape[:2]
        # Scale link_img to match sprite scale
        scaled_size = Vector(lw,lh) * (scale / 100)

        self.link_img = cv2.resize(self.link_img, scaled_size.round(), interpolation=cv2.INTER_AREA)
        #for i in range(-10,10):
        i = 0
        wa = (parent_anchor[0] + i * thickness, parent_anchor[1])

        
        end = (anchor[0]+i*thickness, anchor[1])
        control_points = np.array([wa, 
                                get_point(0.2,wa,-scale*min(2,distance/50)),
                                get_point(0.8,wa,scale*min(2,distance/50)), 
                                end ], np.int32)
        total_length = 0.0
        for i in range(len(control_points) - 1):
            segment_length = np.linalg.norm(control_points[i] - control_points[i + 1])
            total_length += segment_length
        self.bezier_curve_fit(frame_info.render_buffer, control_points, num_points=int(total_length*2.5/scale), color=(0,255,0), thickness=scale)

    def get_custom_inspector(self):
        return [
            {
                "always_showing": True,
                "type": "info",
                "label": "Info",
                "text": "Move a sprite to create a mechanical arm to it.  Adjust the anchor point to position as needed."
            },
            {
                "show_for": "all",
                "label": "Enable Links",
                "type": "checkbox",
                "default": True,
                "sprite_meta": "enable_links"
            },
            {
                "show_for": "all",
                "type": "slider",
                "label": "Link Size",
                "min": 1,
                "max": 99,
                "default": self.default_link_size,
                "sprite_meta": "link_size"
            }
        ]

    def render_frame(self, frame_info: FrameInfo):
        # Get all sprites from sprite manager
        for sprite in self.sprite_manager.sprites:
            if sprite.get_meta("enable_links", True):
                self.render_links(frame_info, sprite)

        super().render_frame(frame_info)

           
        