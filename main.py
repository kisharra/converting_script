from include.convert_class import ConvertTask
from include.convert_class import Get_Info
import subprocess
import json

with open ('config.json', 'r') as config_file:  #read config file
    config = json.load(config_file)
conversion = ConvertTask(config)  #initialize class
get_info = Get_Info(config)
# get_info.get_video_info(config['file_path'])
conversion.convert_files()
