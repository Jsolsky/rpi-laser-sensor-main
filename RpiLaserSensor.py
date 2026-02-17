import cv2
import io
from picamera2 import Picamera2

class RpiLaserSensor:
    def __init__(self):
        self.picam2 = Picamera2()
        self.x = 0
        self.y = 0
        self.image = 0
    
    def read_position_grid(self):

        return self.x, self.y

    def read_position_gauss(self):

        return self.x, self.y
    
    def read_image(self):
        self.picam2.start()

        stream = io.BytesIO()
        self.picam2.capture_file(stream, format="jpeg")

        stream.seek(0) # move to start of stream
        self.img_data = stream.read() # image jpeg data

        print(f"Captured image size: {len(self.img_data)} bytes")
        self.picam2.stop()

        return self.img_data