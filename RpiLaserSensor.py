import cv2
import io
from picamera2 import Picamera2
from PIL import Image
import numpy as np
from matplotlib import pyplot as plt
from PIL import Image
from base64 import b64decode
from scipy.ndimage import gaussian_filter


class RpiLaserSensor:
    def __init__(self):
        self.picam2 = Picamera2()
        self.x = 0
        self.y = 0
        self.image = 0
    
    def read_position_grid(self):

        return self.x, self.y

    def read_position_COM(self):
        """
            This method using a Centre of Mass like method to find the centre position of the beam

            Returns:
                position_x, 
                position_y
        """

        # Read data
        img_data = self.read_image()
        img_pil = Image.open(io.BytesIO(img_data))
        img_array = np.array(img_pil)

        # Channel selection/filtering
        img_array = img_array[:, :, 1]

        # Guassian smoothing (to reduce effect of noise spikes)
        img_array_blurred = gaussian_filter(img_array, sigma=3)

        # Finding pixel under maximum threshold
        img_array_max = (img_array_blurred <= img_array_blurred.max()) & (img_array_blurred > (img_array_blurred.max() - img_array_blurred.max()/4))

        # Find x position
        index_x = np.array(range(0, img_array_max.shape[1]))
        image_array_weighted_x = index_x * img_array_max
        image_array_weighted_x_filtered = image_array_weighted_x[image_array_weighted_x > 0]
        position_x = np.average(image_array_weighted_x_filtered)

        # Find y position
        index_y = np.array(range(0, img_array_max.shape[0]))
        image_array_weighted_y = index_y * img_array_max.transpose() # transposed to rotate 90 degrees
        image_array_weighted_y_filtered = image_array_weighted_y[image_array_weighted_y > 0]
        position_y = np.average(image_array_weighted_y_filtered)

        # Saving figures for debuggins/visualisation
        plt.figure()
        plt.imshow(img_array_blurred)
        plt.scatter(position_x, position_y, color="red", s=4)
        plt.savefig("img_pos.png")
        
        plt.figure
        plt.imshow(img_array_max)
        plt.savefig("img_max.png")

        return position_x, position_y
    
    def read_image(self):
        self.picam2.start()

        stream = io.BytesIO()
        self.picam2.capture_file(stream, format="jpeg")

        stream.seek(0) # move to start of stream
        self.img_data = stream.read() # image jpeg data

        print(f"Captured image size: {len(self.img_data)} bytes")
        self.picam2.stop()

        return self.img_data