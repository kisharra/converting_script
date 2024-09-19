import os
from dotenv import load_dotenv
from conversion.conversion import ConvertTask
import json



def load_config():
    with open (os.path.join('/opt/conversion/settings', 'config.json'), 'r') as config_file:
        config = json.load(config_file)
        load_dotenv(os.path.join(config['path_to_main'], 'settings/.env'))
        config['maria_db']['password'] = os.getenv('DB_PASSWORD')
        return config
    
conversion = ConvertTask(load_config()) 
conversion.parallel_convert()



