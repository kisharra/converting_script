import os
from conversion.conversion import ConvertTask
import json



def load_config(config_file):
    with open ('/opt/converion/settings/config.json', 'r') as config_file:  #read config file
        config = json.load(config_file)
    config['maria_db']['password'] = os.getenv('DB_PASSWORD')
    return config
conversion = ConvertTask(load_config('/opt/converion/settings/config.json'))  #initialize class
conversion.convert_files()



