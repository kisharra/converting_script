import os
from dotenv import load_dotenv
from conversion.directory_converison import ConvertTask
import logging
import json

logging.basicConfig(filename=os.path.join('/opt/conversion/logs', 'convert_logs.log'), level=logging.ERROR, format='%(asctime)s:%(message)s')

def load_config():
    with open (os.path.join('/opt/conversion/settings', 'config.json'), 'r') as config_file:
        config = json.load(config_file)
        load_dotenv(os.path.join(config['path_to_main'], 'settings/.env'))
        config['maria_db']['password'] = os.getenv('DB_PASSWORD')
        return config
    

def get_user_inputs():
    while True:
        try:
            # Insert file path
            directory = input("directory path: ")

            # Check if file exists
            if not os.path.isdir(directory):
                raise ValueError("Directory not found.")
            
            return directory
        except ValueError as e:
            logging.error(f" Attempt to enter directory {directory} failed. Error: {e}")
            print(f"Attempt to enter directory {directory} failed. Error: {e}")

conversion = ConvertTask(load_config()) 

directory = get_user_inputs()

conversion.parallel_convert(directory)