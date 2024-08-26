import os
from conversion.conversion import ConvertTask
from conversion.conversion import Get_Info
from conversion.db_querry import Db_querry
import json

def load_config(config_file):
    with open ('config.json', 'r') as config_file:  #read config file
        config = json.load(config_file)
    config['maria_db']['password'] = os.getenv('DB_PASSWORD')
    return config
conversion = ConvertTask(load_config('config.json'))  #initialize class
get_info = Get_Info(load_config('config.json'))
querry = Db_querry(load_config('config.json'))

# querry.create_table()
get_info.get_video_info(load_config('config.json')['directory'])
# conversion.convert_files()



