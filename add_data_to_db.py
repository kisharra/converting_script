import logging
import os
from conversion.get_info import Get_Info
import json



def load_config():
    with open (os.path.join('/opt/conversion/settings', 'config.json'), 'r') as config_file:
        config = json.load(config_file)
        return config
    
logging.basicConfig(filename=os.path.join('/opt/conversion/logs', 'convert_logs.log'), level=logging.ERROR, format='%(asctime)s:%(message)s')

def get_user_inputs():
    while True:
        try:
            # Insert file path
            file_path = input("Insert file path: ")

            # Check if file exists
            if not os.path.isfile(file_path):
                raise ValueError("File not found.")

            # Insert bool values 1
            bool_value_1_input = input("Insert True if Film, False if Serial: ").strip().lower()
            if bool_value_1_input not in ['true', 'false']:
                raise ValueError("Invalid input. Expected True or False.")
            bool_value_1 = bool_value_1_input == 'true'

            # Insert bool values 2
            bool_value_2_input = input("Insert True if Serial, False if Film: ").strip().lower()
            if bool_value_2_input not in ['true', 'false']:
                raise ValueError("Invalid input. Expected True or False..")
            bool_value_2 = bool_value_2_input == 'true'

            # if all values are valid, return the file path and the bool values
            return file_path, bool_value_1, bool_value_2

        except ValueError as e:
            logging.error(f" Attempt to enter file {file_path} failed. Error: {e}")
            print(f"Attempt to enter file {file_path} failed. Error: {e}")

get_info = Get_Info(load_config())

file_path, bool_value_1, bool_value_2 = get_user_inputs()

get_info.get_single_file_info(file_path, bool_value_1, bool_value_2)

# get_info = Get_Info(load_config())
# get_info.get_all_files_info(load_config()['directory'])


