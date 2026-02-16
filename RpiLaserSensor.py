import cv2

class RpiLaserSensor:
    def __init__(self):

        self.x = 0
        self.y = 0
        self.image = 0
    
    def read_position(self):

        return self.x, self.y
    
    def read_image(self):

        self.img_data = cv2.imread("test-4.jpg")

        return self.img_data