import os
from dotenv import load_dotenv
from conversion.single_conversion import ConvertTask
import json



def load_config():
    with open (os.path.join('/opt/conversion/settings', 'config.json'), 'r') as config_file:
        config = json.load(config_file)
        load_dotenv(os.path.join(config['path_to_main'], 'settings/.env'))
        config['maria_db']['password'] = os.getenv('DB_PASSWORD')
        return config
    
conversion = ConvertTask(load_config()) 
conversion.convert_files(input('Insert file path: '))
