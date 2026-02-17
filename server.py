import time
import socket
from RpiLaserSensor import RpiLaserSensor
import os
from dotenv import load_dotenv
import cv2
from flask import Flask, Response
import base64

# Load variables from .env file
load_dotenv()

print('Initialising sensors')
laser_sensor = RpiLaserSensor() # initialise the sensor
host_address = os.getenv("HOST")
port = os.getenv("PORT")


class SensorServer:
    
    def __init__(self, host=f'{host_address}', port=port):
        self.app = Flask(__name__)
        self.host = host
        self.port = int(port)
        
        self.app.add_url_rule("/image", "image", self.get_image_endpoint)
        self.app.add_url_rule("/position_grid", "position_grid", self.get_position_grid_endpoint)
        self.app.add_url_rule("/position", "position", self.get_position_endpoint)

        self.running = True
        

    def read_sensors_grid(self):

        position_x, position_y = laser_sensor.read_position_grid()
        
        return [position_x, position_y]

    def read_sensors(self):

        position_x, position_y = laser_sensor.read_position_COM()
        
        return [position_x, position_y]

    def read_image(self):

        img_data = laser_sensor.read_image()

        return img_data
        
    def get_image_endpoint(self):

        img_data = self.read_image()
        # _, buffer = cv2.imencode('.jpg', img_data)
        base64_response = base64.b64encode(img_data).decode('utf-8')

        return {"base64":base64_response}
    
    def get_position_grid_endpoint(self):
        position_x, position_y = self.read_sensors_grid()
    
        return {"position_x":position_x, "position_y":position_y}

    def get_position_endpoint(self):
        position_x, position_y = self.read_sensors()
    
        return {"position_x":position_x, "position_y":position_y}

    def start(self):

        print(f"Starting app on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, threaded=True)
        
        
if __name__ == "__main__":
    server = SensorServer()
    try:
        print('Starting server')     
        try:
            server.start()
        except Exception as e:
            print("Failed to start server, error: " + str(e))
            time.sleep(1)
                
    except KeyboardInterrupt:
        print('Keyboard interrupt, stopping server.')
    
    