import cv2
import io
from picamera2 import Picamera2
from PIL import Image
import numpy as np
from matplotlib import pyplot as plt
from PIL import Image
from base64 import b64decode
from scipy.ndimage import gaussian_filter
import time


class RpiLaserSensor:
    def __init__(self):
        self.picam2 = Picamera2()
        self.x = 0
        self.y = 0
        self.image = 0
        self.picam2.start()

    def stop_cam(self):
        self.picam2.stop() # this prints confirmation
    
    def start_cam(self):
        try:
            self.picam2.start()
        except Exception as e:
            print(f"Error: {e}")

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
        try:
            img_data = self.read_image()
        except Exception as e:
            self.picam2.stop()
            self.__init__()

            return None
        
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

        # # Saving figures for debuggins/visualisation
        # plt.figure()
        # plt.imshow(img_array_blurred)
        # plt.scatter(position_x, position_y, color="red", s=4)
        # plt.savefig("img_pos.png")
        
        # plt.figure
        # plt.imshow(img_array_max)
        # plt.savefig("img_max.png")

        return position_x, position_y
    
    def read_image(self):
        try:
            stream = io.BytesIO()
            self.picam2.capture_file(stream, format="jpeg")

            stream.seek(0) # move to start of stream
            self.img_data = stream.read() # image jpeg data
            
            return self.img_data

        except Exception as e:
            self.picam2.stop()
            time.sleep(0.1)
            self.start_cam()

            print(f"Error: {e}")
        
       