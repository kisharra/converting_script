from conversion.get_info import Get_Info
import json



def load_config(config_file):
    with open ('/opt/converion/settings/config.json', 'r') as config_file:  #read config file
        config = json.load(config_file)
    return config

get_info = Get_Info(load_config('/opt/converion/settings/config.json'))
get_info.get_video_info(load_config('/opt/converion/settings/config.json')['directory'])
