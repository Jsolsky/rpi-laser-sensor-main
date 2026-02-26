import cv2
import io
from picamera2 import Picamera2
from PIL import Image
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from PIL import Image
from base64 import b64decode
from scipy.ndimage import gaussian_filter, label
import time


class RpiLaserSensor:
    def __init__(self):
        self.picam2 = Picamera2()
        self.picam2.start()

    def stop_cam(self):
        self.picam2.stop() # this prints confirmation
    
    def start_cam(self):
        try:
            self.picam2.start()
        except Exception as e:
            print(f"Error: {e}")

    def img_data_to_numpy(self, img_data):

        img_pil = Image.open(io.BytesIO(img_data))
        img_array = np.array(img_pil)

        return img_array

    def beam_is_present(self, img_array):
        if img_array[:,:,0].var() <= 100:
            return False
        return True


    def find_grid(self, img_array):
                # Guassian smoothing (to reduce effect of noise spikes)
        img_array_blurred = gaussian_filter(img_array, sigma=3)

        # Finding pixel under maximum threshold
        img_array_max = (img_array_blurred <= img_array_blurred.max()) & (img_array_blurred > (img_array_blurred.max() - img_array_blurred.max()/4))

        labeled_array, num_features = label(img_array_max)
        # we can now find the centre of mass (and total mass) of each cluster

        cluster_indexes = np.unique(labeled_array)
        clusters_df = pd.DataFrame(cluster_indexes[1:], columns=["index"])
        clusters_df[["centre_horizontal", "centre_vertical"]] = clusters_df["index"].apply(lambda x: pd.Series(self.find_COM(labeled_array == x)))
        clusters_df["size"] = clusters_df["index"].apply(lambda x: (labeled_array == x).sum())
        clusters_df["radius_approximation"] = np.sqrt(clusters_df["size"]/np.pi)

        clusters_df = clusters_df[clusters_df["radius_approximation"] > clusters_df["radius_approximation"].max()/3]

        clusters_df.sort_values(by="size", ascending=False, inplace=True)

        clusters_df["is_centre"] = clusters_df["size"] == clusters_df["size"].max()

        def is_above(centre_x, centre_y, target_x, target_y, margin):
            if np.abs(centre_x - target_x) > margin:
                return False
            if centre_y <= target_y:
                return False
            return True

        def is_below(centre_x, centre_y, target_x, target_y, margin):
            if np.abs(centre_x - target_x) > margin:
                return False
            if centre_y >= target_y:
                return False
            return True

        def is_left(centre_x, centre_y, target_x, target_y, margin):
            if np.abs(centre_y - target_y) > margin:
                return False
            if centre_x <= target_x:
                return False
            return True

        def is_right(centre_x, centre_y, target_x, target_y, margin):
            if np.abs(centre_y - target_y) > margin:
                return False
            if centre_x >= target_x:
                return False
            return True

        centre_x = clusters_df[clusters_df["is_centre"] == True].iloc[0]["centre_horizontal"]
        centre_y = clusters_df[clusters_df["is_centre"] == True].iloc[0]["centre_vertical"]

        margin_vertical = 50
        margin_horizontal = 50

        clusters_df["is_above"] = clusters_df.apply(lambda x: is_above(centre_x=centre_x, 
                                                                    centre_y=centre_y,
                                                                    target_x=x["centre_horizontal"],
                                                                    target_y=x["centre_vertical"],
                                                                    margin=margin_vertical), axis=1)

        clusters_df["is_below"] = clusters_df.apply(lambda x: is_below(centre_x=centre_x, 
                                                                    centre_y=centre_y,
                                                                    target_x=x["centre_horizontal"],
                                                                    target_y=x["centre_vertical"],
                                                                    margin=margin_vertical), axis=1)

        clusters_df["is_left"] = clusters_df.apply(lambda x: is_left(centre_x=centre_x, 
                                                                    centre_y=centre_y,
                                                                    target_x=x["centre_horizontal"],
                                                                    target_y=x["centre_vertical"],
                                                                    margin=margin_horizontal), axis=1)

        clusters_df["is_right"] = clusters_df.apply(lambda x: is_right(centre_x=centre_x, 
                                                                    centre_y=centre_y,
                                                                    target_x=x["centre_horizontal"],
                                                                    target_y=x["centre_vertical"],
                                                                    margin=margin_horizontal), axis=1)

        # # Plotting and saving for debugging
        # plt.imshow(img_array_max)
        # plt.scatter(clusters_df[clusters_df["is_above"] == True]["centre_horizontal"], clusters_df[clusters_df["is_above"] == True]["centre_vertical"], color="blue")
        # plt.scatter(clusters_df[clusters_df["is_below"] == True]["centre_horizontal"], clusters_df[clusters_df["is_below"] == True]["centre_vertical"], color="red")
        # plt.scatter(clusters_df[clusters_df["is_left"] == True]["centre_horizontal"], clusters_df[clusters_df["is_left"] == True]["centre_vertical"], color="orange")
        # plt.scatter(clusters_df[clusters_df["is_right"] == True]["centre_horizontal"], clusters_df[clusters_df["is_right"] == True]["centre_vertical"], color="green")
        # plt.savefig("img_grid.png")

               # Find centre using intersection
        x1 = clusters_df[clusters_df["is_above"] == True].iloc[0]["centre_horizontal"]
        y1 = clusters_df[clusters_df["is_above"] == True].iloc[0]["centre_vertical"]
        x2 = clusters_df[clusters_df["is_below"] == True].iloc[0]["centre_horizontal"]
        y2 = clusters_df[clusters_df["is_below"] == True].iloc[0]["centre_vertical"]

        x3 = clusters_df[clusters_df["is_left"] == True].iloc[0]["centre_horizontal"]
        y3 = clusters_df[clusters_df["is_left"] == True].iloc[0]["centre_vertical"]
        x4 = clusters_df[clusters_df["is_right"] == True].iloc[0]["centre_horizontal"]
        y4 = clusters_df[clusters_df["is_right"] == True].iloc[0]["centre_vertical"]

        vertical_line_gradient = (y2-y1)/(x2-x1)
        vertical_line_intercept = y1 - vertical_line_gradient * x1

        horizontal_line_gradient = (y3-y4)/(x3-x4)
        horizontal_line_intercept = y3 - horizontal_line_gradient * x3

        return vertical_line_gradient, vertical_line_intercept, horizontal_line_gradient, horizontal_line_intercept

    def read_position_grid(self):
        """
            This method using a Centre of Mass like method to find the centre position of the beam

            Returns:
                position_x, 
                position_y
        """
        try:
            img_data = self.read_image()
        except Exception as e:
            self.picam2.stop()
            self.__init__()

        img_array = self.img_data_to_numpy(img_data)

        if not self.beam_is_present(img_array):
            return
        
        # Channel selection/filtering
        img_array = img_array[:, :, 1]

        vertical_line_gradient, vertical_line_intercept, horizontal_line_gradient, horizontal_line_intercept = self.find_grid(img_array)
 

        position_x = (vertical_line_intercept - horizontal_line_intercept) / (horizontal_line_gradient - vertical_line_gradient)
        position_y = (vertical_line_gradient * position_x) + vertical_line_intercept

        return position_x, position_y

    def read_grid_full(self):
        """
            This method using a Centre of Mass like method to find the centre position of the beam

            Returns:
                position_x, 
                position_y
        """
        try:
            img_data = self.read_image()
        except Exception as e:
            self.picam2.stop()
            self.__init__()

        img_array = self.img_data_to_numpy(img_data)

        if not self.beam_is_present(img_array):
            return

        # Channel selection/filtering
        img_array = img_array[:, :, 1]

        vertical_line_gradient, vertical_line_intercept, horizontal_line_gradient, horizontal_line_intercept = self.find_grid(img_array)
 

        position_x = (vertical_line_intercept - horizontal_line_intercept) / (horizontal_line_gradient - vertical_line_gradient)
        position_y = (vertical_line_gradient * position_x) + vertical_line_intercept

        return position_x, position_y, vertical_line_gradient, vertical_line_intercept, horizontal_line_gradient, horizontal_line_intercept

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
        
        img_array = self.img_data_to_numpy(img_data)

        if not self.beam_is_present(img_array):
            return

        # Channel selection/filtering
        img_array = img_array[:, :, 1]

             # Guassian smoothing (to reduce effect of noise spikes)
        img_array_blurred = gaussian_filter(img_array, sigma=3)

        # Finding pixel under maximum threshold
        img_array_max = (img_array_blurred <= img_array_blurred.max()) & (img_array_blurred > (img_array_blurred.max() - img_array_blurred.max()/4))

        [position_x, position_y] = self.find_COM(img_array_max)

        # # Saving figures for debuggins/visualisation
        # plt.figure()
        # plt.imshow(img_array_blurred)
        # plt.scatter(position_x, position_y, color="red", s=4)
        # plt.savefig("img_pos.png")
        
        # plt.figure
        # plt.imshow(img_array_max)
        # plt.savefig("img_max.png")

        return position_x, position_y

    def find_COM(self, img_array):

        # Find x position
        index_x = np.array(range(0, img_array.shape[1]))
        image_array_weighted_x = index_x * img_array
        image_array_weighted_x_filtered = image_array_weighted_x[image_array_weighted_x > 0]
        position_x = np.average(image_array_weighted_x_filtered)

        # Find y position
        index_y = np.array(range(0, img_array.shape[0]))
        image_array_weighted_y = index_y * img_array.transpose() # transposed to rotate 90 degrees
        image_array_weighted_y_filtered = image_array_weighted_y[image_array_weighted_y > 0]
        position_y = np.average(image_array_weighted_y_filtered)
    
        return [position_x, position_y]

    
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
        
       