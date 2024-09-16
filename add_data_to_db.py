import os
from conversion.get_info import Get_Info
import json



def load_config():
    with open (os.path.join('/opt/conversion/settings', 'config.json'), 'r') as config_file:
        config = json.load(config_file)
        return config

get_info = Get_Info(load_config())
get_info.get_single_file_info('/storage/A/Avatar.2009.BDRip.1080p.Rus.Eng.mkv', True, False)
# get_info.get_single_file_info('/storage/S/Stephen.Hawking/SHGD1.mkv', False, True)
