import time
import socket
from RpiLaserSensor import RpiLaserSensor
import os
from dotenv import load_dotenv
import cv2
from flask import Flask, Response
import base64
from waitress import serve
import logging
from paste.translogger import TransLogger

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
        
        self.app.add_url_rule("/init_test", "init_test", self.picam_start)
        self.app.add_url_rule("/image", "image", self.get_image_endpoint)
        self.app.add_url_rule("/position_grid", "position_grid", self.get_position_grid_endpoint)
        self.app.add_url_rule("/position_grid_full", "position_grid_full", self.get_grid_full_endpoint)

        # Change this back later
        # self.app.add_url_rule("/position", "position", self.get_position_endpoint)
        self.app.add_url_rule("/position", "position", self.get_position_grid_endpoint)

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
        
        try:
            position_x, position_y = self.read_sensors_grid()
        
            return {"position_x":position_x, "position_y":position_y}
        except Exception as e:
            print(f"Error {e}")
            return {"position_x":None, "position_y":None}


    def get_position_endpoint(self):

        try:
            position_x, position_y = self.read_sensors()
        
            return {"position_x":position_x, "position_y":position_y}
        except Exception as e:
            print(f"Error {e}")
            return {"position_x":None, "position_y":None}

    def picam_start(self):
        print("start init")
        laser_sensor.start_cam()
        print("complete init")

        return {"Status":"Complete"}


    def get_grid_full_endpoint(self):

        try:
            position_x, position_y, vertical_line_gradient, vertical_line_intercept, horizontal_line_gradient, horizontal_line_intercept = laser_sensor.read_grid_full()
        
            return {
                "position_x":position_x,  
                "position_y":position_y,
                "vertical_line_gradient":vertical_line_gradient, 
                "vertical_line_intercept":vertical_line_intercept, 
                "horizontal_line_gradient":horizontal_line_gradient, 
                "horizontal_line_intercept":horizontal_line_intercept
            } 
        except Exception as e:
            print(f"Error: {e}")
        
        return {
                "position_x":None,  
                "position_y":None,
                "vertical_line_gradient":None, 
                "vertical_line_intercept":None, 
                "horizontal_line_gradient":None, 
                "horizontal_line_intercept":None
            } 

    def start(self):
        print(f"Starting app on {self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port, threaded=True)

    def stop(self):
        try:
            laser_sensor.stop()
            self.running = False
        except Exception as e:
            self.running = False


def get_local_time(timestamp):

    tz = pytz.timezone('Australia/Sydney') 
    dt = datetime.datetime.fromtimestamp(timestamp, tz)
    return dt.timetuple()

# 2. Patch the logging formatter converter
        
if __name__ == "__main__":
    server = SensorServer()
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    logging.Formatter.converter = get_local_time

    try: 
        print('Starting server')     
        serve(TransLogger(server.app, setup_console_handler=False), host=server.host, port=server.port)
    except KeyboardInterrupt:
        server.stop()
    # except Exception as e:
    #     print(f"Error: {e}")

    
    