from package.conversion import ConvertTask
from package.conversion import Get_Info
from package.db_querry import Db_querry
import json

with open ('config.json', 'r') as config_file:  #read config file
    config = json.load(config_file)
conversion = ConvertTask(config)  #initialize class
get_info = Get_Info(config)
querry = Db_querry(config)

# get_info.get_video_info(config['directory'])
conversion.convert_files()



